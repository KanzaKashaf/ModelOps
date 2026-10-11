"""Tests for Prometheus metrics exposure."""

VALID_FEATURES = [8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]


def test_metrics_endpoint_returns_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_include_custom_prediction_counter(client):
    client.post("/v1/predict", json={"features": VALID_FEATURES})
    response = client.get("/metrics")
    assert "modelops_predictions_total" in response.text


def test_metrics_include_inference_duration(client):
    client.post("/v1/predict", json={"features": VALID_FEATURES})
    response = client.get("/metrics")
    assert "modelops_inference_duration_seconds" in response.text
