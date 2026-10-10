"""Reproducible training script with MLflow tracking and model registration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from modelops.data.loader import SEED, TARGET_COLUMN, load_dataset
from modelops.data.split import split_dataset
from modelops.data.validation import validate_dataset
from modelops.tracking.config import ensure_experiment, set_tracking_uri
from modelops.tracking.metadata import collect_run_metadata
from modelops.training.preprocessing import build_preprocessor, get_feature_columns

ARTIFACT_DIR = Path("models")
REPORT_DIR = Path("reports")
REGISTERED_MODEL_NAME = "modelops-housing-regressor"


def _evaluate(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _build_model(model_name: str, seed: int):
    if model_name == "baseline_dummy":
        return DummyRegressor(strategy="mean")
    if model_name == "ridge":
        return Ridge(alpha=1.0, random_state=seed)
    if model_name == "gradient_boosting":
        return GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.1, random_state=seed
        )
    raise ValueError(f"Unknown model: {model_name}")


def train_and_log(model_name: str, train_df, test_df, run_metadata: dict) -> dict:
    """Train, evaluate, log to MLflow, and register a model."""
    features = get_feature_columns(list(train_df.columns))
    estimator = _build_model(model_name, SEED)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(features)),
            ("model", estimator),
        ]
    )

    X_train, y_train = train_df[features], train_df[TARGET_COLUMN]
    X_test, y_test = test_df[features], test_df[TARGET_COLUMN]

    with mlflow.start_run(run_name=model_name) as run:
        # Reproducibility tags
        for key, value in run_metadata.items():
            mlflow.set_tag(key, str(value))

        # Hyperparameters
        if model_name == "gradient_boosting":
            mlflow.log_params(
                {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.1}
            )
        elif model_name == "ridge":
            mlflow.log_param("alpha", 1.0)
        mlflow.log_param("seed", SEED)
        mlflow.log_param("model_name", model_name)

        pipeline.fit(X_train, y_train)

        train_metrics = _evaluate(y_train, pipeline.predict(X_train))
        test_metrics = _evaluate(y_test, pipeline.predict(X_test))

        for prefix, metrics in [("train", train_metrics), ("test", test_metrics)]:
            for metric_name, value in metrics.items():
                mlflow.log_metric(f"{prefix}_{metric_name}", value)

        # # Log the full pipeline (preprocessing + model) and register it
        # mlflow.sklearn.log_model(
        #     sk_model=pipeline,
        #     artifact_path="model",
        #     registered_model_name=REGISTERED_MODEL_NAME,
        # )

        # Log the full pipeline (preprocessing + model) and register it
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            name="model",                          # was artifact_path="model"
            registered_model_name=REGISTERED_MODEL_NAME,
            serialization_format="cloudpickle",    # <-- add this line
        )

        # Local joblib copy for offline use and manifest checksums
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, ARTIFACT_DIR / f"{model_name}.joblib", protocol=5)

        return {
            "run_id": run.info.run_id,
            "model_name": model_name,
            "train": train_metrics,
            "test": test_metrics,
            "seed": SEED,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="ModelOps MLflow training")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    set_tracking_uri()
    ensure_experiment()

    print("Loading and validating dataset...")
    df = load_dataset()
    df = validate_dataset(df)
    train_df, test_df = split_dataset(df, test_size=args.test_size, seed=args.seed)

    run_metadata = collect_run_metadata(train_df, test_df)
    print(f"Git commit: {run_metadata['git_commit']}")
    print(f"Train hash: {run_metadata['train_data_hash'][:16]}...")

    all_results = {}
    for model_name in ["baseline_dummy", "ridge", "gradient_boosting"]:
        print(f"Training and logging {model_name}...")
        result = train_and_log(model_name, train_df, test_df, run_metadata)
        all_results[model_name] = result
        print(f"  Run ID: {result['run_id']}")
        print(f"  Test MAE: {result['test']['mae']:.4f}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "mlflow_runs.json").write_text(json.dumps(all_results, indent=2))

    # Generate manifests for each trained model
    from modelops.tracking.manifest import (
        build_manifest,
        get_registered_version,
        write_manifest,
    )

    manifest_paths = {}
    for model_name, result in all_results.items():
        version = get_registered_version(result["run_id"], REGISTERED_MODEL_NAME)
        local_artifact = ARTIFACT_DIR / f"{model_name}.joblib"
        manifest = build_manifest(
            model_name=model_name,
            run_id=result["run_id"],
            registered_model_version=version,
            local_artifact_path=local_artifact,
            train_data_hash=run_metadata["train_data_hash"],
            test_metrics=result["test"],
        )
        manifest_path = write_manifest(manifest)
        manifest_paths[model_name] = str(manifest_path)
        print(f"Manifest written: {manifest_path}")

    (REPORT_DIR / "manifests.json").write_text(json.dumps(manifest_paths, indent=2))
    print("Done. Open MLflow UI at http://127.0.0.1:5000")


if __name__ == "__main__":
    main()
