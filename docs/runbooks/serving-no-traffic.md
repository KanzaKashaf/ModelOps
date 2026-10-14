# Runbook: No Prediction Traffic

## Alert

ServingNoPredictionTraffic

## Symptom

No prediction requests received in the last 10 minutes.

## Impact

May indicate a legitimate idle period, an upstream client failure,
or a network problem. Informational.

## Diagnosis

1. Confirm the metric is flat:
   curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(modelops_predictions_total[10m]))' | python3 -m json.tool
2. Confirm the container is running:
   docker compose ps serving
3. Send a manual prediction:
   curl -s -X POST http://localhost:8000/v1/predict \
     -H "Content-Type: application/json" \
     -d '{"features": [8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]}'
4. Check upstream client logs.

## Likely Causes

| Cause | Mitigation |
|-------|------------|
| Idle period | No action |
| Client stopped | Restart client, check client errors |
| Network issue | Verify DNS and TCP reachability |
| Changed URL | Update client config |

## Mitigation

For legitimate idle periods, no action. The alert resolves when
traffic resumes.

## Verification

Send a manual prediction and confirm:
1. Alert transitions to inactive within 30 seconds.
2. modelops_predictions_total increments.
