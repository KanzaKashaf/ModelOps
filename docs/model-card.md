# Model Card — Gradient Boosting Regressor

## Model Details
- Type: GradientBoostingRegressor (scikit-learn)
- Version: 0.1.0
- Trained: (fill in date from metrics)
- Artifact: `models/gradient_boosting.joblib`
- Pipeline: median imputation → standard scaling → gradient boosting

## Intended Use
- Prediction of median house value for California census block groups.
- Educational / portfolio demonstration only. **Not for real estate decisions.**

## Training Data
- California Housing dataset (20,640 samples, 8 features).
- Train/test split: 80/20 with seed 42.
- Preprocessing fitted **only** on training split.

## Evaluation
- Baseline (DummyRegressor): MAE ≈ 0.9061
- Ridge: MAE ≈ 0.5332
- Gradient Boosting: MAE ≈ 0.3484

## Limitations
- Data is from 1990; predictions do not reflect current markets.
- Target is capped at $500,001, limiting upper-range accuracy.
- No categorical features in this dataset; pipeline structure is
  extensible but untested on categorical data.
- Spatial autocorrelation not modelled; random split may overestimate
  generalisation to unseen geographic areas.



## Registered Model

- MLflow model name: `modelops-housing-regressor`
- Current champion version: v9 (gradient_boosting)
- Champion alias: `@champion`
- MLflow tracking URI: `http://127.0.0.1:5000`
- Manifest: `manifests/gradient_boosting-v9.json`
- Artifact SHA-256: `39e692462c0cb483246d641dbc758756c88a4a776f078d74d98a6d86b5949f61`
- Train data hash: `12bfd88874257882278818367f28bb018f80ad6397a0ad57fc1c652060ce8a72`

## Promotion History (local)

| Version | Model             | Test MAE | Promoted At            | Decision  |
|---------|-------------------|----------|------------------------|-----------|
| v9      | gradient_boosting | 0.3484   | 2026-10-10T20:07:43Z   | Approved  |
| v8      | ridge             | 0.5332   | N/A                    | Rejected  |
| v7      | baseline_dummy    | 0.9061   | N/A                    | Rejected  |

Rejection reasons are recorded in `reports/promotion_log.jsonl`.