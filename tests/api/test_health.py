"""Contract tests for health and metadata endpoints."""


def test_liveness_always_returns_200(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_returns_200_when_model_loaded(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["model_loaded"] is True


def test_model_info_returns_expected_fields(client):
    response = client.get("/v1/model/info")
    assert response.status_code == 200
    body = response.json()
    assert body["model_name"] == "modelops-housing-regressor"
    assert isinstance(body["features"], list)
    assert len(body["features"]) == 8
    assert body["target"] == "MedHouseValue"
    assert "model_version" in body
    assert "model_uri" in body
    assert "loaded_at" in body


def test_root_returns_service_info(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "service" in body
    assert "version" in body
