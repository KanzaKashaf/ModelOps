# Incident Postmortem: Phase 10 Failure Drills

## Date
2026-10-20

## Summary
Executed eight controlled failure drills against the local Docker Compose environment. Most drills produced the expected symptoms and were successfully recovered. Due to a recent Docker data purge, the MLflow registry and local manifests were empty, requiring the drills to be adapted to test the fallback and recovery mechanics.

## Drill Results

| # | Drill | Expected Symptom | Detected? | Alert Fired | Recovery | Verified |
|---|-------|------------------|-----------|-------------|----------|----------|
| 1 | Invalid image tag | Container fails to pull | Yes | N/A | N/A (real container unaffected) | Yes |
| 2 | Container stop | API unreachable | Yes | ServingNoPredictionTraffic | `docker compose start` | Yes |
| 3 | Model unavailable | Readiness 503 | Yes | ServingModelLoadFailures | Restore artifact | Yes |
| 4 | Malformed inputs | 4xx responses | Yes | N/A (metrics only) | N/A | Yes |
| 5 | Latency breach | P95 > 500ms | Yes | ServingHighLatencyP95 | End load test | Yes |
| 6 | Failed promotion | Gate rejects | Yes | N/A (audit log) | N/A | Yes |
| 7 | Data drift | drift_share > 0.3 | Yes | ServingHighDataDrift | Push clean data | Yes |
| 8 | Rollback | Version changes | Yes | modelops_model_info | Alias retarget | Yes |

## Lessons Learned

1. **Prometheus `up == 0` is essential for container-down detection.**
   `rate(metric[10m])` returns no data when a target disappears, causing alerts to miss the outage. The explicit `up == 0` clause (added in Phase 9) fixed this.

2. **Read-only mounts provide defense in depth.**
   Drill 3 confirmed that the model artifact is mounted read-only and cannot be modified from inside the container. Recovery required modifying the host file and restarting.

3. **Resource limits are necessary for 8 GB hardware.**
   The k6 load test with 50 VUs caused memory pressure. The Compose resource limits (512 MB per container) prevented OOM-killing other services.

4. **The promotion gate is deterministic and auditable.**
   Drill 6 confirmed that a model failing quality thresholds cannot be promoted, and the rejection is recorded in `reports/promotion_log.jsonl`.

5. **Data drift alerts must be accompanied by runbooks.**
   Drill 7 confirmed that the drift alert fires, but the runbook is what tells the operator what to do next. Data drift is not proof of accuracy decline.

## Action Items

| Action | Owner | Status |
|--------|-------|--------|
| Document all drill results | KanzaKashaf | Done |
| Verify alert → runbook references | KanzaKashaf | Done |
| Re-populate MLflow registry post-purge | KanzaKashaf | Pending |
