# Runbook: Serving High Latency (P95)

## Alert

ServingHighLatencyP95

## Symptom

The 95th percentile inference latency exceeds 500 ms.

## Impact

Slow responses degrade user experience and may cause client timeouts.

## Diagnosis

1. Check the Grafana dashboard: ModelOps Serving Overview -> P95 Latency panel.
2. Check container CPU usage:
   docker stats modelops-serving --no-stream
3. Check host swap usage:
   free -h
4. Time a single prediction:
   time curl -s -X POST http://localhost:8000/v1/predict \
     -H "Content-Type: application/json" \
     -d '{"features": [8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]}'
5. Query the histogram: modelops_inference_duration_seconds_bucket

## Likely Causes

| Cause | Mitigation |
|-------|------------|
| Host swapping | Increase Docker memory or close other apps |
| CPU contention | Reduce concurrency or add CPU |
| Model larger than expected | Verify model file size |
| Abnormal input payloads | Validate input ranges |

## Mitigation

Reduce load: stop any running load tests.

Restart:
   docker compose restart serving

Horizontal scaling requires a reverse proxy in front of the Compose
service. Documented as future work.

## Verification

1. P95 latency returns below 500 ms in Grafana.
2. Alert transitions to inactive in Prometheus.