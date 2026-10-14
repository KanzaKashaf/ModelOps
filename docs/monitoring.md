# Monitoring and Observability

The ModelOps platform runs its observability stack on Docker Compose.
Prometheus scrapes the serving API and the Pushgateway, Grafana
displays dashboards, and Evidently computes drift metrics for the
monitoring pipeline.

## Architecture
serving (FastAPI) pushgateway prometheus grafana
:8000/metrics <---- :9091 <---- push :9090 -----> :3000
^ ^ |
| | |
+-- scraped by -------+-- scraped by --------+-- queried by --+

text

- **serving** exposes custom Prometheus metrics on `/metrics`
- **pushgateway** receives drift metrics from the Evidently job
- **prometheus** scrapes both and evaluates alert rules
- **grafana** visualizes the metrics using provisioned dashboards

## Ports

| Service | Host port | Purpose |
|---------|-----------|---------|
| serving | 8000 | Prediction API |
| mlflow | 5000 | MLflow tracking server |
| prometheus | 9090 | Metrics store + UI |
| pushgateway | 9091 | Receives batch-pushed metrics |
| grafana | 3000 | Dashboards (admin / `GRAFANA_ADMIN_PASSWORD`) |

## Metric Inventory

### Application metrics (from `src/modelops/serving/app.py`)

| Metric | Type | Labels |
|--------|------|--------|
| `modelops_predictions_total` | counter | `model_name`, `model_version` |
| `modelops_inference_duration_seconds` | histogram | `model_name` |
| `modelops_model_load_failures_total` | counter | — |
| `modelops_model_info` | gauge | `model_name`, `model_version`, `source` |

### HTTP-level metrics (from `prometheus-fastapi-instrumentator`)

| Metric | Type |
|--------|------|
| `http_requests_total` | counter |
| `http_request_duration_seconds` | histogram |
| `http_request_size_bytes` | histogram |
| `http_response_size_bytes` | histogram |

### Drift metrics (pushed to Pushgateway)

| Metric | Type | Source |
|--------|------|--------|
| `modelops_drift_share` | gauge | Evidently drift job |
| `modelops_drifted_columns` | gauge | Evidently drift job |
| `modelops_total_columns` | gauge | Evidently drift job |

## Alert Inventory

All rules live in `monitoring/alerts/serving-alerts.yaml`.

| Alert | Severity | Trigger |
|-------|----------|---------|
| `ServingHighErrorRateFastBurn` | critical | 5xx rate > 14.4% for 2m |
| `ServingHighErrorRateSlowBurn` | warning | 5xx rate > 6% for 30m |
| `ServingHighLatencyP95` | warning | P95 latency > 500ms for 5m |
| `ServingModelLoadFailures` | critical | Any model load failure in 5m |
| `ServingNoPredictionTraffic` | warning | No traffic OR scrape target down for 10m |
| `ServingHighDataDrift` | warning | Drift share > 0.3 for 5m |

See [docs/slo.md](slo.md) for SLO definitions and burn-rate math.

## Runbooks

| Alert | Runbook |
|-------|---------|
| High error rate | [serving-high-error-rate.md](runbooks/serving-high-error-rate.md) |
| High latency | [serving-high-latency.md](runbooks/serving-high-latency.md) |
| Model not loaded | [serving-model-not-loaded.md](runbooks/serving-model-not-loaded.md) |
| No traffic | [serving-no-traffic.md](runbooks/serving-no-traffic.md) |
| Data drift | [serving-data-drift.md](runbooks/serving-data-drift.md) |

## Dashboards

Grafana dashboards are provisioned as code from `monitoring/dashboards/`.
The Compose file mounts this directory into Grafana at
`/var/lib/grafana/dashboards`; a provider config at
`docker/grafana/provisioning/dashboards/dashboards.yml` loads them.

The main dashboard is **ModelOps Serving Overview** with panels for:
request rate, error rate, P95 latency, predictions by model version,
model info, load failures, prediction rate, and drift share.

## Drift Detection Workflow

The reference dataset is the training split (16,512 rows). Recent data
is compared against it using Evidently's `DataDriftPreset`.

```bash
# Save the reference dataset
python -m modelops.monitoring.reference

# Generate a synthetic "drifted" dataset for testing
python -m modelops.monitoring.synthetic_drift

# Run the drift check and push metrics to the Pushgateway
python -m modelops.monitoring.drift --recent data/recent_drifted.parquet
The drift job writes reports/drift_report.html (full report) and
reports/drift_report.json (machine-readable summary), then pushes
three gauges to the Pushgateway. Prometheus scrapes the Pushgateway
with honor_labels: true, preserving the job="modelops_drift" label.

Data drift is not proof of accuracy decline. The drift alert is
informational. See docs/runbooks/serving-data-drift.md for the
correct workflow.

Controlled Failure Exercises
See docs/incidents/2026-10-14-controlled-failure-exercises.md
for two verified drills:

Data drift alert fired and resolved.

Container-down alert fired and resolved.

Common Commands
bash
# Bring up the full stack
docker compose up -d

# Check service health
docker compose ps
curl http://localhost:8000/health/ready

# Open the UIs
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000
# MLflow:     http://localhost:5000

# Query the current drift share
HOST_IP=$(ip route show default | awk '{print $3}')
curl -s "http://${HOST_IP}:9090/api/v1/query?query=modelops_drift_share"

# List currently firing alerts
curl -s "http://${HOST_IP}:9090/api/v1/alerts" | python3 -m json.tool
Troubleshooting
Symptom	Cause	Fix
Grafana returns 401	Wrong password	Check GRAFANA_ADMIN_PASSWORD in .env or use admin
Prometheus target down	Serving container stopped	docker compose up -d serving
Drift metric not visible	Pushgateway not scraped	Verify honor_labels: true in docker/prometheus.yml
Alert never fires	for: duration not elapsed	Check /api/v1/rules for pending state
n_columns wrong count	Target column included in drift	Verify drift.py drops TARGET_COLUMN