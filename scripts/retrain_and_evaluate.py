"""Manual retraining and candidate evaluation workflow.

This script:
1. Validates the current dataset against the Pandera schema.
2. Trains candidate models using the existing training pipeline.
3. Evaluates each candidate against the promotion gate.
4. Writes a human-readable evaluation report.
5. Does NOT promote automatically. Promotion is a separate,
   human-initiated step using scripts/promote_model.py.

Usage:
    python scripts/retrain_and_evaluate.py
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from modelops.data.loader import load_dataset
from modelops.data.split import split_dataset
from modelops.data.validation import validate_dataset
from modelops.governance.promotion import PromotionPolicy, evaluate_promotion
from modelops.tracking.config import ensure_experiment
from modelops.tracking.manifest import build_manifest, get_registered_version, write_manifest
from modelops.tracking.metadata import collect_run_metadata
from modelops.training.train_mlflow import REGISTERED_MODEL_NAME, train_and_log

REPORT_DIR = Path("reports")
MANIFEST_DIR = Path("manifests")


def run_retraining(seed: int = 42) -> dict:
    """Run the full retraining and evaluation workflow."""
    ensure_experiment()

    # 1. Load and validate data
    print("Loading and validating dataset...")
    df = load_dataset()
    df = validate_dataset(df)
    train_df, test_df = split_dataset(df, seed=seed)
    run_metadata = collect_run_metadata(train_df, test_df)
    print(f"Data validated: {len(train_df)} train / {len(test_df)} test rows")

    # 2. Train candidates
    results = {}
    for model_name in ["baseline_dummy", "ridge", "gradient_boosting"]:
        print(f"Training {model_name}...")
        result = train_and_log(model_name, train_df, test_df, run_metadata)
        results[model_name] = result
        print(f"  Test MAE: {result['test']['mae']:.4f}")

    # 3. Generate manifests
    manifest_paths = {}
    for model_name, result in results.items():
        version = get_registered_version(result["run_id"], REGISTERED_MODEL_NAME)
        local_artifact = Path("models") / f"{model_name}.joblib"
        manifest = build_manifest(
            model_name=model_name,
            registered_model_name=REGISTERED_MODEL_NAME,
            run_id=result["run_id"],
            registered_model_version=version,
            local_artifact_path=local_artifact,
            train_data_hash=run_metadata["train_data_hash"],
            test_metrics=result["test"],
        )
        manifest_path = write_manifest(manifest, MANIFEST_DIR)
        manifest_paths[model_name] = str(manifest_path)

    # 4. Evaluate promotion gate for each candidate
    policy = PromotionPolicy()
    evaluations = {}
    for model_name, manifest_path in manifest_paths.items():
        decision = evaluate_promotion(manifest_path, policy)
        evaluations[model_name] = {
            "manifest_path": manifest_path,
            "approved": decision.approved,
            "reasons": decision.reasons,
            "metrics": decision.candidate_metrics,
            "champion_metrics": decision.champion_metrics,
        }

    # 5. Write evaluation report
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "seed": seed,
        "train_data_hash": run_metadata["train_data_hash"],
        "git_commit": run_metadata["git_commit"],
        "evaluations": evaluations,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "retraining_evaluation.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nEvaluation report written to {report_path}")

    # 6. Print summary
    print("\n" + "=" * 60)
    print("CANDIDATE EVALUATION SUMMARY")
    print("=" * 60)
    for model_name, ev in evaluations.items():
        status = "APPROVED" if ev["approved"] else "REJECTED"
        print(f"\n{model_name}: {status}")
        print(f"  Metrics: {ev['metrics']}")
        if ev["reasons"]:
            for reason in ev["reasons"]:
                print(f"  - {reason}")

    print("\n" + "=" * 60)
    print("NEXT STEP: Human review of the evaluation report.")
    print("If approved, run:")
    print(f"  python scripts/promote_model.py {manifest_paths['gradient_boosting']}")
    print("Then restart the serving container:")
    print("  docker compose restart serving")
    print("=" * 60)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retrain and evaluate candidates")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_retraining(seed=args.seed)
