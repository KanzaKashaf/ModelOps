# Runbook: Serving High Error Rate

## Alert

- `ServingHighErrorRateFastBurn` (critical)
- `ServingHighErrorRateSlowBurn` (warning)

## Symptom

The serving API is returning HTTP 5xx responses at a rate that
consumes the availability error budget faster than sustainable.

## Impact

Clients receive errors instead of predictions. If the fast-burn alert
is firing, the 30-day error budget will be exhausted in ~2 days.

## Diagnosis

1. Confirm the alert in Prometheus: http://localhost:9090/alerts
2. Check the Grafana dashboard: ModelOps Serving Overview -> Error Rate panel.
3. Inspect container logs:
   docker compose logs serving --tail=100
4. Verify the serving API is up:
   curl -s http://localhost:8000/health/live
   curl -s http://localhost:8000/health/ready
5. Check container resource usage:
   docker stats modelops-serving --no-stream
6. Check MLflow reachability:
   docker compose exec serving curl -s http://mlflow:5000/health

## Likely Causes

| Symptom in logs | Cause | Mitigation |
|-----------------|-------|------------|
| ModuleNotFoundError | Bad image build | Roll back to previous image |
| RuntimeError: Could not load model | Model artifact missing | Verify /app/models/, verify MLflow |
| HTTPException: 500 | Application code error | Inspect traceback, fix, redeploy |
| MemoryError | Memory pressure | Increase limits |

## Mitigation

Restart the serving container:
   docker compose restart serving

Roll back to a previous image:
   cd ~/ModelOps
   git checkout <previous-commit-sha>
   ./scripts/build_image.sh
   docker compose up -d serving

Retarget the champion alias in MLflow:
   python -c "from mlflow.tracking import MlflowClient; \
     MlflowClient().set_registered_model_alias( \
       name='modelops-housing-regressor', alias='champion', version=1)"

## Verification

1. Error rate drops below 1% on the Grafana dashboard.
2. Alert transitions from firing to inactive in Prometheus.
3. /health/ready returns 200.

## Escalation

If the error rate does not recover within 15 minutes, escalate with
the alert name, last 100 log lines, and the current error rate.