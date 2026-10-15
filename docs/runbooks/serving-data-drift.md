# Runbook: Serving Data Drift

## Alert

ServingHighDataDrift

## Symptom

The share of features whose distribution has shifted exceeds 30%.
Metric: modelops_drift_share, produced by the Evidently drift job.

## Impact

Input distributions have changed. This does NOT prove that model
accuracy has declined. Accuracy can only be assessed when fresh
ground-truth labels are available.

## Diagnosis

1. Open the latest Evidently HTML report: reports/drift_report.html
2. Identify which features drifted and by how much.
3. Classify the drift: transient (one-off batch) or systematic
   (upstream pipeline change, schema change, seasonal effect).
4. Compare reference and recent distributions in the report.
5. Check upstream data sources for schema or source changes.

## Likely Causes

| Cause | Mitigation |
|-------|------------|
| Pipeline change | Update pipeline, re-validate |
| Schema change | Update loader and schema |
| Seasonal effect | No action unless accuracy declines |
| Collection bug | Fix source, backfill |
| Population shift | Evaluate retraining need |

## Mitigation

Transient: no action.

Systematic without accuracy impact: update the reference dataset to
the new baseline and re-run the drift check.

Systematic with proven accuracy decline: retrain, evaluate, promote
through the Phase 2 gate.

## Important

Data drift alone is not sufficient justification for retraining.
The correct workflow:
1. Detect drift (this alert).
2. Collect fresh ground-truth labels.
3. Compute accuracy on labelled recent data.
4. If accuracy declined, trigger retraining.
5. Evaluate on the same held-out test set.
6. Pass the promotion gate.
7. Promote.

## Verification

1. modelops_drift_share drops below 0.3 after mitigation.
2. Alert transitions to inactive in Prometheus.
