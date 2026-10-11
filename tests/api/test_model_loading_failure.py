"""Tests for model-loading failure behaviour.

Uses ``broken_client``, whose app has no valid model source, so the
loader raises, ``model_loaded`` stays False, and readiness is 503.
"""


def test_readiness_returns_503_when_model_missing(broken_client):
    response = broken_client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["model_loaded"] is False
    assert body["status"] == "not_ready"


def test_liveness_still_returns_200_when_model_missing(broken_client):
    response = broken_client.get("/health/live")
    assert response.status_code == 200


def test_predict_returns_503_when_model_missing(broken_client):
    response = broken_client.post(
        "/v1/predict", json={"features": [1.0] * 8}
    )
    assert response.status_code == 503


def test_model_info_returns_503_when_model_missing(broken_client):
    response = broken_client.get("/v1/model/info")
    assert response.status_code == 503
