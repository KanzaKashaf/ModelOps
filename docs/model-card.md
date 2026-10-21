# Model Card — Gradient Boosting Regressor

## Model Details
- **Type:** `GradientBoostingRegressor` (scikit-learn)
- **Registered model:** `modelops-housing-regressor`
- **Current champion version:** v3 (from `@champion` alias)
- **Artifact:** `models/gradient_boosting.joblib` (SHA-256 recorded in manifest)
- **Pipeline:** Median imputation → Standard scaling → Gradient Boosting
- **Trained:** 2026-10-21

## Intended Use
- Prediction of median house value for California census block groups.
- Educational / portfolio demonstration only. **Not for real estate decisions.**

## Training Data
- California Housing dataset (20,640 samples, 8 numeric features).
- 1990 U.S. census data. See `docs/data-card.md` for provenance and limitations.
- Train/test split: 80/20 with seed 42. Preprocessing fitted only on the training split.

## Evaluation (Latest Retraining)
| Model | Test MAE | Test RMSE | Test R² | Promotion |
|-------|----------|-----------|---------|-----------|
| baseline_dummy | 0.9061 | 1.1449 | -0.0002 | Rejected |
| ridge | 0.5332 | 0.7456 | 0.5758 | Rejected |
| gradient_boosting | **0.3484** | **0.5114** | **0.8004** | **Approved** |

## Limitations
- Data from 1990; predictions do not reflect current markets.
- Target capped at $500,001.
- Spatial autocorrelation not modelled.
- Data drift alerts do not prove accuracy decline.

## Registered Model
- **MLflow model name:** `modelops-housing-regressor`
- **Current champion version:** v3 (gradient_boosting)
- **Champion alias:** `@champion`
- **Manifest:** `manifests/gradient_boosting-v3.json`
- **Artifact SHA-256:** *(See manifest file for exact hash)*
- **Train data hash:** `12bfd88874257882278818367f28bb018f80ad6397a0ad57fc1c652060ce8a72`

## Promotion History
| Version | Model | Test MAE | Decision |
|---------|-------|----------|----------|
| v3 | gradient_boosting | 0.3484 | Approved |
| v2 | ridge | 0.5332 | Rejected |
| v1 | baseline_dummy | 0.9061 | Rejected |

Rejection reasons are recorded in `reports/promotion_log.jsonl`.
