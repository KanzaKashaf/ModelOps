# Postmortem: Controlled Failure Exercises

**Date:** 2026-10-14
**Author:** KanzaKashaf
**Status:** Resolved

## Summary

Two controlled failures were introduced to verify the observability
stack detects, alerts on, and reports recovery from adverse conditions.
Both alerts fired, both resolved, and no impact occurred outside the
test scope.

## Exercise 1 - Data Drift

**Failure:** Synthetic recent dataset with four of eight features
shifted (MedInc 2x, HouseAge 1.8x, AveRooms 0.5x, AveOccup 3x).

**Detection:** ServingHighDataDrift fired. Time to fire: 5 minutes.

**Impact:** None. Serving API continued responding.

**Resolution:** Pushed a clean recent dataset; drift share returned to 0.

**Recovery:** Alert firing -> inactive in under 1 minute.

**Lessons:** The alert description explicitly states drift does not
prove accuracy decline. This prevents operators from retraining on
drift alone.

## Exercise 2 - Serving Container Down

**Failure:** Stopped the serving container with `docker compose stop serving`.

**Detection:** ServingNoPredictionTraffic fired. Time to fire: 10 minutes.

**Impact:** No predictions served for the duration.

**Root cause:** Deliberate test.

**Resolution:** Restarted the container and sent predictions to restore traffic.

**Recovery:** Alert firing -> inactive in under 1 minute.

**Lessons:** The alert initially missed the container-down case because
`rate(modelops_predictions_total[10m])` returns no data (not zero)
when the target disappears. The rule was updated to add an explicit
`up{job="modelops-serving"} == 0` clause.

## Actions

- [x] Both alerts verified firing.
- [x] Both alerts verified resolving.
- [x] Recovery under 5 minutes in both cases.
- [x] Runbooks exist for both alerts.
- [ ] Add Alertmanager for notification routing (deferred).
