import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// ── Custom metrics ──────────────────────────────────────────────
const errorRate = new Rate('modelops_loadtest_error_rate');
const predictionLatency = new Trend('modelops_loadtest_prediction_latency');

// ── Test configuration ──────────────────────────────────────────
export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '10s',
      exec: 'smokeTest',
      tags: { scenario: 'smoke' },
    },
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 10 },  // Ramp up to 10 VUs
        { duration: '30s', target: 10 },   // Hold at 10 VUs
        { duration: '10s', target: 0 },    // Ramp down
      ],
      exec: 'loadTest',
      startTime: '15s',  // Start after smoke test completes
      tags: { scenario: 'load' },
    },
  },
  thresholds: {
    'http_req_duration{scenario:load}': ['p(95)<500'],  // P95 < 500ms
    'modelops_loadtest_error_rate': ['rate<0.01'],       // Error rate < 1%
    'http_req_failed{scenario:load}': ['rate<0.01'],     // HTTP failures < 1%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const VALID_PAYLOAD = JSON.stringify({
  features: [8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23],
});

export function smokeTest() {
  const res = http.get(`${BASE_URL}/health/live`);
  check(res, {
    'smoke: liveness 200': (r) => r.status === 200,
  });
  sleep(1);
}

export function loadTest() {
  const headers = { 'Content-Type': 'application/json' };

  const res = http.post(`${BASE_URL}/v1/predict`, VALID_PAYLOAD, { headers });

  const success = check(res, {
    'predict: status 200': (r) => r.status === 200,
    'predict: has prediction': (r) => {
      try {
        return JSON.parse(r.body).prediction !== undefined;
      } catch {
        return false;
      }
    },
    'predict: has request_id': (r) => {
      try {
        return JSON.parse(r.body).request_id !== undefined;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!success);
  predictionLatency.add(res.timings.duration);

  sleep(0.1);
}
