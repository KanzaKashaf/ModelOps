# Service Level Objectives

These SLOs are **learning targets**, not production commitments. They
are calibrated for a single-node local environment and will need to
be re-tuned against real traffic in any deployment.

## 1. Availability

| Attribute | Value |
|-----------|-------|
| Target | 99% of requests return a non-5xx response |
| Window | 30 days rolling |
| Error budget | 1% (~7.2 hours of 5xx-equivalent downtime) |
| Measurement | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` |

## 2. Latency

| Attribute | Value |
|-----------|-------|
| Target | P95 inference latency < 500 ms |
| Window | 5-minute rolling |
| Error budget | 5% of requests may exceed the threshold |
| Measurement | `histogram_quantile(0.95, sum(rate(modelops_inference_duration_seconds_bucket[5m])) by (le))` |

## 3. Error Rate

| Attribute | Value |
|-----------|-------|
| Target | < 1% of requests return 5xx |
| Window | 30 days rolling |
| Error budget | 1% of requests |
| Measurement | Same expression as availability, inverted |

## 4. Recovery

| Attribute | Value |
|-----------|-------|
| Target | Recovery from a detected incident < 5 minutes |
| Window | Per incident |
| Measurement | Time from alert firing to alert resolving |

---

## Multi-Window Burn-Rate Alerts

A single-threshold alert (e.g. "error rate > 1% for 5m") fires on every
transient spike. A multi-window burn-rate alert fires only when the
error budget is being consumed at an unsustainable rate.

| Alert | Long window | Short window | Burn rate | Time to exhaust 30-day budget | Severity |
|-------|-------------|--------------|-----------|-------------------------------|----------|
| `ServingHighErrorRateFastBurn` | 1h | 5m | 14.4x | ~2 days | critical |
| `ServingHighErrorRateSlowBurn` | 6h | 30m | 6x | ~5 days | warning |

The multipliers are derived from the SLO target. For a 99% SLO:

- A **14.4x** burn rate consumes 2% of the 30-day budget in 1 hour.
- A **6x** burn rate consumes 5% of the 30-day budget in 6 hours.

Both alerts must be firing for their `for:` duration before notifying.
This is the pattern from the Google SRE Workbook.

---

## Operational Alerts (not SLO-based)

These alerts indicate specific operational problems rather than
budget consumption.

| Alert | Expression | Severity |
|-------|------------|----------|
| `ServingModelLoadFailures` | `increase(modelops_model_load_failures_total[5m]) > 0` | critical |
| `ServingNoPredictionTraffic` | `sum(rate(modelops_predictions_total[10m])) == 0` | warning |

---

## Data Drift

Data drift is **measured** but is **not** an SLO.

- **Metric:** `modelops_drift_share` — the share of features whose
  distribution has shifted compared to the reference (training) dataset.
- **Alert threshold:** > 0.3 for 5 minutes.
- **Severity:** warning.

**Important:** data drift indicates that the input distribution has
changed. It does not prove that the model's predictions are wrong.
Accuracy can only be assessed when fresh ground-truth labels are
available. The `ServingHighDataDrift` alert must never be treated as
equivalent to an accuracy SLO violation.

---

## Alertmanager

No Alertmanager is deployed in the Compose-based Phase 9 setup. Alerts
are visible in the Prometheus UI at `/alerts`. To add notifications
(email, Slack, PagerDuty), deploy Alertmanager and configure
`alerting:` in `docker/prometheus.yml`. This is documented as a
future-work item.

---

## Runbooks

Every alert references a runbook:

- `ServingHighErrorRateFastBurn` / `ServingHighErrorRateSlowBurn` → [serving-high-error-rate.md](runbooks/serving-high-error-rate.md)
- `ServingHighLatencyP95` → [serving-high-latency.md](runbooks/serving-high-latency.md)
- `ServingModelLoadFailures` → [serving-model-not-loaded.md](runbooks/serving-model-not-loaded.md)
- `ServingNoPredictionTraffic` → [serving-no-traffic.md](runbooks/serving-no-traffic.md)
- `ServingHighDataDrift` → [serving-data-drift.md](runbooks/serving-data-drift.md)
