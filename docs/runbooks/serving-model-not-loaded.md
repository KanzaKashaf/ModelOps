# Runbook: Model Not Loaded

## Alert

ServingModelLoadFailures

## Symptom

The serving API recorded one or more model loading failures. The
modelops_model_load_failures_total counter incremented.

## Impact

If the model fails to load, /health/ready returns 503. Clients cannot
receive predictions.

## Diagnosis

1. Check readiness:
   curl -s http://localhost:8000/health/ready
2. Inspect serving logs:
   docker compose logs serving --tail=50
3. Verify model file:
   docker compose exec serving ls -la /app/models/
4. Verify environment variables:
   docker compose exec serving env | grep MODELOPS
5. Check MLflow:
   curl -s http://localhost:5000/health

## Likely Causes

| Cause | Mitigation |
|-------|------------|
| Model missing at /app/models/ | Restore the file or fix the mount |
| MLflow unreachable | Verify MLflow container is up |
| Registry alias missing | Set MODELOPS_MODEL_URI="" to force local fallback |
| Corrupt model file | Re-run training to regenerate |
| Image missing model | Rebuild image |

## Mitigation

Fall back to local artifact: set MODELOPS_MODEL_URI="" and
MODELOPS_MLFLOW_TRACKING_URI="" in docker-compose.yml, then
docker compose up -d serving.

Restore the model:
   docker compose cp models/gradient_boosting.joblib serving:/app/models/
   docker compose restart serving

Restart MLflow:
   docker compose up -d mlflow

## Verification

1. /health/ready returns 200.
2. modelops_model_info = 1 in Prometheus.
3. Serving logs show no load failure.