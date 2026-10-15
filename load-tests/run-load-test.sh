#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "Running load test against ${BASE_URL}"

K6_PROMETHEUS_RW_SERVER_URL="${K6_PROMETHEUS_RW_SERVER_URL:-http://localhost:9090/api/v1/write}" \
K6_PROMETHEUS_RW_TIMEOUT="30s" \
K6_PROMETHEUS_RW_TREND_STATS="p(95),p(99),min,max,avg" \
k6 run \
  --out experimental-prometheus-rw \
  load-tests/serving-load-test.js

echo "Load test complete. Check Grafana for k6 metrics."
