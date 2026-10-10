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