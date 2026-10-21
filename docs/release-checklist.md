# Model Release Checklist

Use this checklist before promoting a candidate model to `@champion`.

## 1. Retraining Completed

- [ ] `python scripts/retrain_and_evaluate.py` ran successfully.
- [ ] `reports/retraining_evaluation.json` exists and contains the candidate metrics.
- [ ] The candidate passes all absolute thresholds (MAE ≤ 0.40, RMSE ≤ 0.60, R² ≥ 0.70).
- [ ] The candidate does not regress against the current champion by more than 0.02 MAE.

## 2. Human Review

- [ ] A human reviewer has read `reports/retraining_evaluation.json`.
- [ ] The reviewer confirms the candidate metrics are acceptable.
- [ ] The reviewer checks that the training data hash matches the expected dataset version.
- [ ] The reviewer checks that the Git commit in the report matches the current `main`.

## 3. Promotion

- [ ] `python scripts/promote_model.py manifests/gradient_boosting-v<N>.json` was run.
- [ ] The promotion log (`reports/promotion_log.jsonl`) records the approval.
- [ ] The `@champion` alias points to the new version in MLflow.

## 4. Serving Update

- [ ] `docker compose restart serving` was run to reload the model.
- [ ] `/v1/model/info` shows the new model version.
- [ ] A sample prediction request returns a valid response.
- [ ] Grafana shows the new model version in the `modelops_model_info` gauge.

## 5. Rollback Plan

- [ ] The previous champion version is known and recorded.
- [ ] If the new model causes issues, `python scripts/promote_model.py` with the previous version's manifest, then restart serving.
- [ ] The rollback procedure is documented in `docs/runbooks/serving-model-not-loaded.md`.

## 6. Communication

- [ ] The team is notified of the model update.
- [ ] The model card is updated with the new version and metrics.
- [ ] The incident postmortem template is ready if issues arise.
