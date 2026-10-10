# Model Governance Guide

This document defines how models are evaluated, versioned, promoted,
and rolled back in the ModelOps platform. Governance is deterministic:
identical inputs always produce identical decisions.

## 1. Model Registry

All trained models are registered in MLflow under the name
`modelops-housing-regressor`. Each registration creates a new
immutable version number (v1, v2, v3, ...). Versions are never
mutated; only their aliases change.

## 2. Aliases (replacing stages)

| Alias         | Meaning                                              |
|---------------|------------------------------------------------------|
| `@champion`   | Currently approved and deployed model                |
| `@challenger` | Candidate under evaluation (optional, for A/B tests) |

Aliases replace the deprecated `Staging` and `Production` stages.
Aliases are atomic: retargeting `@champion` from v3 to v4 does not
mutate v3.

Reserved alias names that MLflow rejects: `latest`, `v1`, `v2`, etc.
Use descriptive names only.

## 3. Promotion Policy

A candidate model is promoted to `@champion` only if **all** of the
following are true:

| Criterion                        | Threshold |
|----------------------------------|-----------|
| Test MAE                         | ≤ 0.40    |
| Test RMSE                        | ≤ 0.60    |
| Test R²                          | ≥ 0.70    |
| MAE regression vs current champ  | ≤ 0.02    |

The first promotion (no current champion) is evaluated only against
absolute thresholds. After a champion exists, the relative criterion
applies.

Thresholds are configurable via `PromotionPolicy` but must never be
weakened without a documented justification and a renewed evaluation
of the currently deployed champion.

## 4. Promotion Workflow

1. Train candidate models: `python -m modelops.training.train_mlflow`
2. Manifests are written to `manifests/<model>-v<N>.json`.
3. Evaluate dry-run:
   `python scripts/promote_model.py manifests/<file>.json --dry-run`
4. If approved, promote:
   `python scripts/promote_model.py manifests/<file>.json`
5. Verify in MLflow UI under Models → `modelops-housing-regressor`.

Promotion is a **human-initiated** action. CI may evaluate the gate
but must not promote automatically.

## 5. Model Manifest

Every candidate has a manifest in `manifests/`. The manifest is the
single source of truth for what the model is, what it was evaluated
against, and what bytes were produced.

Required fields:

```json
{
  "schema_version": "1.1.0",
  "model_name": "gradient_boosting",
  "registered_model_name": "modelops-housing-regressor",
  "mlflow_run_id": "<32-char hex>",
  "registered_model_version": 9,
  "artifact_path": "models/gradient_boosting.joblib",
  "artifact_sha256": "<64-char hex>",
  "train_data_hash": "<64-char hex>",
  "test_metrics": {"mae": 0.3484, "rmse": 0.5114, "r2": 0.8004},
  "dependencies": {"scikit_learn": "1.9.1", "...": "..."},
  "python_version": "3.12.5",
  "platform": "Windows-...",
  "created_at": "2026-...Z",
  "tracking_uri": "http://127.0.0.1:5000"
}
