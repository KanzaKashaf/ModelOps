"""Tests for the model loader's pure helpers and fallback logic.

These tests do not require a live MLflow server. Where a fallback is
being tested, ``mlflow.sklearn.load_model`` is monkeypatched to raise
immediately so we do not exercise MLflow's network retry backoff.
"""
from __future__ import annotations

import joblib
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline

from modelops.data.loader import TARGET_COLUMN, load_dataset
from modelops.data.split import split_dataset
from modelops.serving.model_loader import load_model, resolve_model_version
from modelops.training.preprocessing import build_preprocessor, get_feature_columns

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

SAMPLE_FEATURES = [8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]


def _sample_df() -> pd.DataFrame:
    """Return a one-row DataFrame with the training feature column names."""
    return pd.DataFrame([SAMPLE_FEATURES], columns=FEATURE_NAMES)


# ---------------------------------------------------------------------------
# resolve_model_version
# ---------------------------------------------------------------------------


def test_resolve_version_unknown_for_file_uri():
    assert resolve_model_version("file:///tmp/foo.joblib", "any") == "unknown"


def test_resolve_version_from_versioned_uri():
    # ``models:/name/3`` — no MLflow call needed
    assert resolve_model_version("models:/some-model/3", "some-model") == "v3"


def test_resolve_version_from_alias_degrades_when_offline(monkeypatch):
    """If the alias cannot be resolved (offline), return 'unknown'."""
    from mlflow.tracking import MlflowClient

    def boom(self, name, alias):  # noqa: ANN001, ARG001
        raise RuntimeError("offline")

    monkeypatch.setattr(MlflowClient, "get_model_version_by_alias", boom)
    assert (
        resolve_model_version("models:/nonexistent@champion", "nonexistent")
        == "unknown"
    )


# ---------------------------------------------------------------------------
# load_model — fixture and fallback tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tiny_pipeline():
    """A minimal sklearn Pipeline for fallback testing."""
    df = load_dataset()
    train_df, _ = split_dataset(df, test_size=0.2, seed=42)
    train_df = train_df.head(200)
    features = get_feature_columns(list(train_df.columns))
    pipe = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(features)),
            ("model", Ridge(alpha=1.0, random_state=42)),
        ]
    )
    pipe.fit(train_df[features], train_df[TARGET_COLUMN])
    return pipe


@pytest.fixture
def registry_unavailable(monkeypatch):
    """Make mlflow.sklearn.load_model raise immediately (no network)."""

    def boom(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
        raise RuntimeError("simulated: registry unreachable")

    import mlflow.sklearn

    monkeypatch.setattr(mlflow.sklearn, "load_model", boom)


def test_load_model_uses_local_fallback_when_registry_unavailable(
    tmp_path, tiny_pipeline, registry_unavailable
):
    artifact = tmp_path / "tiny.joblib"
    joblib.dump(tiny_pipeline, artifact)

    loaded = load_model(
        model_uri="models:/definitely-does-not-exist@champion",
        model_name="definitely-does-not-exist",
        local_fallback=artifact,
        tracking_uri="http://127.0.0.1:59999",  # unused; mocked
    )
    assert loaded.source == "local_fallback"
    assert loaded.model_version == "local-fallback"

    pred = loaded.model.predict(_sample_df())
    assert pred.shape == (1,)


def test_load_model_raises_when_both_sources_fail(tmp_path, registry_unavailable):
    with pytest.raises(RuntimeError):
        load_model(
            model_uri="models:/nope@champion",
            model_name="nope",
            local_fallback=tmp_path / "missing.joblib",
            tracking_uri="http://127.0.0.1:59999",  # unused; mocked
        )
