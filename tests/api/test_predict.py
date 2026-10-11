"""Contract tests for the prediction endpoint."""
from __future__ import annotations

import pandas as pd

VALID_FEATURES = [8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]

FEATURE_NAMES = [
    "MedInc",
    "HouseAge",
    "AveRooms",
    "AveBedrms",
    "Population",
    "AveOccup",
    "Latitude",
    "Longitude",
]


def test_valid_prediction_returns_typed_response(client):
    response = client.post("/v1/predict", json={"features": VALID_FEATURES})
    assert response.status_code == 200
    body = response.json()
    for key in ("request_id", "model_name", "model_version", "prediction", "inference_ms"):
        assert key in body
    assert isinstance(body["prediction"], float)
    assert 0.0 <= body["prediction"] <= 6.0
    assert body["inference_ms"] >= 0.0


def test_response_includes_request_id_header(client):
    response = client.post("/v1/predict", json={"features": VALID_FEATURES})
    assert "X-Request-ID" in response.headers


def test_request_id_in_body_matches_header(client):
    response = client.post("/v1/predict", json={"features": VALID_FEATURES})
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_missing_feature_rejected(client):
    response = client.post("/v1/predict", json={"features": [1.0, 2.0, 3.0]})
    assert response.status_code == 422


def test_extra_feature_rejected(client):
    response = client.post("/v1/predict", json={"features": VALID_FEATURES + [1.0]})
    assert response.status_code == 422


def test_wrong_dtype_rejected(client):
    response = client.post(
        "/v1/predict",
        json={"features": ["a", "b", "c", "d", "e", "f", "g", "h"]},
    )
    assert response.status_code == 422


def test_extra_field_rejected(client):
    response = client.post(
        "/v1/predict",
        json={"features": VALID_FEATURES, "unexpected": 1},
    )
    assert response.status_code == 422


def test_empty_features_rejected(client):
    response = client.post("/v1/predict", json={"features": []})
    assert response.status_code == 422


def test_prediction_matches_direct_model_call(client, tiny_model):
    """Model-contract test: API prediction must match direct model prediction."""
    import joblib

    model = joblib.load(tiny_model)
    sample_df = pd.DataFrame([VALID_FEATURES], columns=FEATURE_NAMES)
    expected = float(model.predict(sample_df)[0])

    response = client.post("/v1/predict", json={"features": VALID_FEATURES})
    assert response.status_code == 200
    actual = response.json()["prediction"]
    assert abs(actual - expected) < 1e-9
