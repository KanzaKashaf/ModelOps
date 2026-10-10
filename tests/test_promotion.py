"""Tests for the model promotion gate.

These tests do not require a live MLflow server. When the server is
unreachable, ``_get_champion_metrics`` returns None and the gate falls
back to absolute thresholds only.
"""
import json
from pathlib import Path

from modelops.governance.promotion import PromotionPolicy, evaluate_promotion


def _write_manifest(tmp_path: Path, model_name: str, metrics: dict) -> Path:
    manifest = {
        "schema_version": "1.1.0",
        "model_name": model_name,
        "registered_model_name": "test-registered-model",
        "test_metrics": metrics,
        "artifact_sha256": "abc123",
        "mlflow_run_id": "run-123",
        "registered_model_version": 1,
    }
    path = tmp_path / f"{model_name}-manifest.json"
    path.write_text(json.dumps(manifest))
    return path


def test_good_candidate_passes_absolute_gates(tmp_path):
    manifest = _write_manifest(
        tmp_path, "test-good", {"mae": 0.30, "rmse": 0.45, "r2": 0.85}
    )
    decision = evaluate_promotion(manifest, PromotionPolicy())
    assert decision.approved
    assert decision.reasons == []


def test_high_mae_rejected(tmp_path):
    manifest = _write_manifest(
        tmp_path, "test-high-mae", {"mae": 0.55, "rmse": 0.70, "r2": 0.60}
    )
    decision = evaluate_promotion(manifest, PromotionPolicy())
    assert not decision.approved
    assert any("MAE" in r for r in decision.reasons)


def test_low_r2_rejected(tmp_path):
    manifest = _write_manifest(
        tmp_path, "test-low-r2", {"mae": 0.30, "rmse": 0.45, "r2": 0.50}
    )
    decision = evaluate_promotion(manifest, PromotionPolicy())
    assert not decision.approved
    assert any("R2" in r for r in decision.reasons)


def test_high_rmse_rejected(tmp_path):
    manifest = _write_manifest(
        tmp_path, "test-high-rmse", {"mae": 0.35, "rmse": 0.75, "r2": 0.80}
    )
    decision = evaluate_promotion(manifest, PromotionPolicy())
    assert not decision.approved
    assert any("RMSE" in r for r in decision.reasons)


def test_multiple_failures_reported(tmp_path):
    manifest = _write_manifest(
        tmp_path, "test-multi", {"mae": 0.60, "rmse": 0.80, "r2": 0.40}
    )
    decision = evaluate_promotion(manifest, PromotionPolicy())
    assert not decision.approved
    assert len(decision.reasons) >= 2


def test_policy_thresholds_are_configurable(tmp_path):
    # A model that would fail the default policy passes a looser one
    manifest = _write_manifest(
        tmp_path, "test-loose", {"mae": 0.55, "rmse": 0.70, "r2": 0.60}
    )
    strict = evaluate_promotion(manifest, PromotionPolicy())
    loose = evaluate_promotion(
        manifest,
        PromotionPolicy(max_mae=0.60, max_rmse=0.75, min_r2=0.55),
    )
    assert not strict.approved
    assert loose.approved
