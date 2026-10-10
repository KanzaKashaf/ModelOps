"""Deterministic model promotion gate.

The gate evaluates a candidate model against quality thresholds and
the current champion. If the candidate passes, it is promoted to the
``@champion`` alias. If it fails, promotion is blocked with a clear
reason list.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from mlflow.tracking import MlflowClient


@dataclass
class PromotionPolicy:
    """Quality thresholds for promotion."""

    max_mae: float = 0.40
    max_rmse: float = 0.60
    min_r2: float = 0.70
    max_mae_regression_vs_champion: float = 0.02
    require_beats_champion: bool = True


@dataclass
class PromotionDecision:
    """Result of a promotion evaluation."""

    approved: bool
    reasons: list[str] = field(default_factory=list)
    candidate_metrics: dict = field(default_factory=dict)
    champion_metrics: dict | None = None


def _get_champion_metrics(model_name: str) -> dict | None:
    """Return the current champion's test metrics, or None if no champion."""
    client = MlflowClient()
    try:
        champion_version = client.get_model_version_by_alias(model_name, "champion")
    except Exception:
        return None

    try:
        champion_run = client.get_run(champion_version.run_id)
    except Exception:
        return None

    return {
        "mae": champion_run.data.metrics.get("test_mae"),
        "rmse": champion_run.data.metrics.get("test_rmse"),
        "r2": champion_run.data.metrics.get("test_r2"),
    }


def evaluate_promotion(
    candidate_manifest_path: Path | str,
    policy: PromotionPolicy | None = None,
) -> PromotionDecision:
    """Evaluate whether a candidate model should be promoted."""
    policy = policy or PromotionPolicy()
    manifest = json.loads(Path(candidate_manifest_path).read_text())
    candidate_metrics = manifest["test_metrics"]
    reasons: list[str] = []

    # Absolute quality gates
    if candidate_metrics["mae"] > policy.max_mae:
        reasons.append(
            f"MAE {candidate_metrics['mae']:.4f} exceeds max {policy.max_mae}"
        )
    if candidate_metrics["rmse"] > policy.max_rmse:
        reasons.append(
            f"RMSE {candidate_metrics['rmse']:.4f} exceeds max {policy.max_rmse}"
        )
    if candidate_metrics["r2"] < policy.min_r2:
        reasons.append(
            f"R2 {candidate_metrics['r2']:.4f} below min {policy.min_r2}"
        )

    # Compare against current champion
    champion_metrics = _get_champion_metrics(manifest["registered_model_name"])
    if champion_metrics and policy.require_beats_champion:
        champion_mae = champion_metrics.get("mae")
        if champion_mae is not None:
            regression = candidate_metrics["mae"] - champion_mae
            if regression > policy.max_mae_regression_vs_champion:
                reasons.append(
                    f"Candidate MAE regresses by {regression:.4f} "
                    f"(max allowed {policy.max_mae_regression_vs_champion})"
                )

    return PromotionDecision(
        approved=len(reasons) == 0,
        reasons=reasons,
        candidate_metrics=candidate_metrics,
        champion_metrics=champion_metrics,
    )


def promote_candidate(
    model_name: str,
    candidate_version: int,
    decision: PromotionDecision,
) -> None:
    """Promote a candidate to @champion if approved; raise otherwise."""
    if not decision.approved:
        raise ValueError(
            f"Promotion blocked for {model_name} v{candidate_version}: "
            + "; ".join(decision.reasons)
        )
    client = MlflowClient()
    client.set_registered_model_alias(
        name=model_name,
        alias="champion",
        version=candidate_version,
    )
    print(f"Promoted {model_name} v{candidate_version} to @champion")
