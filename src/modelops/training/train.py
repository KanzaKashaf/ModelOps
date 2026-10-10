"""Reproducible training script for baseline and candidate models."""
from __future__ import annotations

import argparse
import json
import platform
import random
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from modelops.data.loader import SEED, TARGET_COLUMN, load_dataset
from modelops.data.split import split_dataset
from modelops.data.validation import validate_dataset
from modelops.training.preprocessing import build_preprocessor, get_feature_columns

ARTIFACT_DIR = Path("models")
REPORT_DIR = Path("reports")


def _set_global_seeds(seed: int) -> None:
    """Pin all global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def evaluate(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def train_model(
    model_name: str,
    estimator,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> dict:
    """Train, evaluate, and save a single model pipeline."""
    features = get_feature_columns(list(train_df.columns))
    preprocessor = build_preprocessor(features)

    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", estimator)])

    x_train = train_df[features]
    y_train = train_df[TARGET_COLUMN]
    x_test = test_df[features]
    y_test = test_df[TARGET_COLUMN]

    pipeline.fit(x_train, y_train)

    train_pred = pipeline.predict(x_train)
    test_pred = pipeline.predict(x_test)

    metrics = {
        "model_name": model_name,
        "train": evaluate(y_train, train_pred),
        "test": evaluate(y_test, test_pred),
        "seed": SEED,
        "git_commit": _git_commit(),
        "python_version": platform.python_version(),
        "timestamp": datetime.now(UTC).isoformat(),
        "n_train": len(train_df),
        "n_test": len(test_df),
    }

    artifact_path = ARTIFACT_DIR / f"{model_name}.joblib"
    joblib.dump(pipeline, artifact_path, protocol=5)
    metrics["artifact_path"] = str(artifact_path)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="ModelOps training pipeline")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    _set_global_seeds(args.seed)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading dataset...")
    df = load_dataset()
    df = validate_dataset(df)
    print(f"Dataset validated: {df.shape}")

    train_df, test_df = split_dataset(df, test_size=args.test_size, seed=args.seed)
    print(f"Train: {train_df.shape}, Test: {test_df.shape}")

    models = {
        "baseline_dummy": DummyRegressor(strategy="mean"),
        "ridge": Ridge(alpha=1.0, random_state=args.seed),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.1,
            random_state=args.seed,
        ),
    }

    all_metrics = {}
    for name, estimator in models.items():
        print(f"Training {name}...")
        metrics = train_model(name, estimator, train_df, test_df)
        all_metrics[name] = metrics
        print(f"  Test MAE: {metrics['test']['mae']:.4f}")

    report_path = REPORT_DIR / "training_metrics.json"
    report_path.write_text(json.dumps(all_metrics, indent=2))
    print(f"Metrics written to {report_path}")


if __name__ == "__main__":
    main()
