"""Fixtures for the serving API tests.

Two fixtures are provided:

- ``tiny_model``: a small in-test scikit-learn pipeline saved to a
  temporary joblib file. Used as the local fallback so contract
  tests never touch the real champion artifact or a live MLflow server.
- ``client``: a FastAPI ``TestClient`` whose app loads ``tiny_model``
  via ``MODELOPS_LOCAL_ARTIFACT_FALLBACK``. The ``MODEL_URI`` override
  points at a non-existent file URI, which MLflow rejects quickly
  (no network call), so the loader falls through to the local file.
- ``broken_client``: a client whose app cannot load any model, so
  readiness returns 503.
"""
from __future__ import annotations

import joblib
import pytest
from fastapi.testclient import TestClient

from modelops.data.loader import TARGET_COLUMN, load_dataset
from modelops.data.split import split_dataset
from modelops.training.preprocessing import build_preprocessor, get_feature_columns


@pytest.fixture(scope="session")
def tiny_model(tmp_path_factory):
    """Train a tiny Ridge pipeline and return its joblib path."""
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline

    df = load_dataset()
    train_df, _ = split_dataset(df, test_size=0.2, seed=42)
    train_df = train_df.head(500)
    features = get_feature_columns(list(train_df.columns))

    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(features)),
            ("model", Ridge(alpha=1.0, random_state=42)),
        ]
    )
    pipeline.fit(train_df[features], train_df[TARGET_COLUMN])

    path = tmp_path_factory.mktemp("models") / "tiny_ridge.joblib"
    joblib.dump(pipeline, path)
    return path


@pytest.fixture
def client(tiny_model, monkeypatch, tmp_path):
    """Return a TestClient whose app loads a local fallback model."""
    # Point the registry URI at a non-existent local file so MLflow
    # fails fast without making network calls.
    monkeypatch.setenv(
        "MODELOPS_MODEL_URI", f"file://{tmp_path}/does-not-exist"
    )
    monkeypatch.setenv("MODELOPS_LOCAL_ARTIFACT_FALLBACK", str(tiny_model))

    from modelops.serving.config import get_settings

    get_settings.cache_clear()

    from modelops.serving.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture
def broken_client(monkeypatch, tmp_path):
    """Return a TestClient whose app cannot load any model."""
    monkeypatch.setenv(
        "MODELOPS_MODEL_URI", f"file://{tmp_path}/does-not-exist"
    )
    monkeypatch.setenv(
        "MODELOPS_LOCAL_ARTIFACT_FALLBACK", str(tmp_path / "missing.joblib")
    )

    from modelops.serving.config import get_settings

    get_settings.cache_clear()

    from modelops.serving.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
