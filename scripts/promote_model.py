"""CLI to evaluate and promote a model candidate.

Usage:
    python scripts/promote_model.py manifests/gradient_boosting-v6.json
    python scripts/promote_model.py manifests/ridge-v5.json --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure the src layout is importable even without an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from modelops.governance.promotion import (  # noqa: E402
    PromotionPolicy,
    evaluate_promotion,
    promote_candidate,
)


def _append_audit_log(entry: dict, log_path: Path = Path("reports/promotion_log.jsonl")) -> None:
    """Append a single JSON line to the promotion audit log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Model promotion gate")
    parser.add_argument("manifest", type=Path, help="Path to model manifest JSON")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate only")
    parser.add_argument("--max-mae", type=float, default=0.40)
    parser.add_argument("--max-rmse", type=float, default=0.60)
    parser.add_argument("--min-r2", type=float, default=0.70)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    policy = PromotionPolicy(
        max_mae=args.max_mae,
        max_rmse=args.max_rmse,
        min_r2=args.min_r2,
    )

    decision = evaluate_promotion(args.manifest, policy)

    # Audit log: capture every decision, including dry-runs
    log_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "manifest_path": str(args.manifest),
        "model_name": manifest["model_name"],
        "registered_model_version": manifest.get("registered_model_version"),
        "approved": decision.approved,
        "reasons": decision.reasons,
        "candidate_metrics": decision.candidate_metrics,
        "champion_metrics": decision.champion_metrics,
        "dry_run": args.dry_run,
    }
    _append_audit_log(log_entry)

    print(f"Model: {manifest['model_name']}")
    print(f"Candidate metrics: {decision.candidate_metrics}")
    if decision.champion_metrics:
        print(f"Champion metrics: {decision.champion_metrics}")
    else:
        print("Champion metrics: (none)")
    print(f"Approved: {decision.approved}")
    for reason in decision.reasons:
        print(f"  - {reason}")

    if args.dry_run:
        return 0 if decision.approved else 1

    if not decision.approved:
        print("Promotion blocked.")
        return 1

    promote_candidate(
        model_name=manifest["registered_model_name"],
        candidate_version=manifest["registered_model_version"],
        decision=decision,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
