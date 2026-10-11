r"""Integration tests that require a live MLflow server.

Skipped automatically when MLflow is not reachable, so the default
local and CI runs stay fast and offline-friendly. Start MLflow
(``.\scripts\start_mlflow.ps1`` on Windows, or
``python -m mlflow server ...`` in WSL) to exercise the real
champion model end-to-end.
"""
from __future__ import annotations

import urllib.request

import pandas as pd
import pytest

from modelops.serving.config import get_settings


def _mlflow_reachable() -> bool:
    try:
        url = get_settings().mlflow_tracking_uri + "/health"
        urllib.request.urlopen(url, timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _mlflow_reachable(),
        reason="MLflow tracking server not reachable",
    ),
]

FEATURE_COLUMNS = [
    "MedInc",
    "HouseAge",
    "AveRooms",
    "AveBedrms",
    "Population",
    "AveOccup",
    "Latitude",
    "Longitude",
]


def test_real_champion_loads_from_registry():
    from modelops.serving.model_loader import load_model

    settings = get_settings()
    loaded = load_model(
        model_uri=settings.model_uri,
        model_name=settings.model_name,
        local_fallback=None,  # force registry-only
        tracking_uri=settings.mlflow_tracking_uri,
    )
    assert loaded.source == "mlflow_registry"
    assert loaded.model_version.startswith("champion@")
    assert hasattr(loaded.model, "predict")


def test_real_champion_serves_prediction():
    from modelops.serving.model_loader import load_model

    settings = get_settings()
    loaded = load_model(
        model_uri=settings.model_uri,
        model_name=settings.model_name,
        local_fallback=None,
        tracking_uri=settings.mlflow_tracking_uri,
    )
    sample = pd.DataFrame(
        [[8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]],
        columns=FEATURE_COLUMNS,
    )
    prediction = loaded.model.predict(sample)
    assert prediction.shape == (1,)
    assert 0.0 <= float(prediction[0]) <= 6.0
