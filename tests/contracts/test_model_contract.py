"""Model-contract tests.

Verify that the served model's schema and metadata match the
training contract. These catch silent drift where a model is
retrained with different features but the API schema is not updated.

The contract is defined by:
- Feature names and order (from the training pipeline / Pandera schema).
- Target name.
- Feature count enforced by the API request schema.

These tests do NOT require a live MLflow server. They use the
Pandera schema and the Pydantic request schema as the two ends of
the contract.
"""
from __future__ import annotations

import pydantic
import pytest

from modelops.data.loader import TARGET_COLUMN
from modelops.data.validation import HousingSchema
from modelops.serving.schemas import PredictRequest

# The canonical feature order, derived from the training pipeline.
EXPECTED_FEATURES = [
    "MedInc",
    "HouseAge",
    "AveRooms",
    "AveBedrms",
    "Population",
    "AveOccup",
    "Latitude",
    "Longitude",
]

EXPECTED_TARGET = "MedHouseValue"
EXPECTED_FEATURE_COUNT = 8


def test_feature_order_matches_training_schema():
    """Training schema and contract share the same feature order."""
    schema = HousingSchema.to_schema()
    training_features = [c for c in schema.columns if c != TARGET_COLUMN]
    assert training_features == EXPECTED_FEATURES


def test_target_name_matches_training_schema():
    """The target column name is stable across the codebase."""
    assert TARGET_COLUMN == EXPECTED_TARGET


def test_expected_feature_count_is_consistent():
    """The constant used by the API matches the training feature count."""
    assert len(EXPECTED_FEATURES) == EXPECTED_FEATURE_COUNT


def test_predict_request_accepts_correct_feature_count():
    """The API request schema enforces exactly EXPECTED_FEATURE_COUNT.

    We assert via the JSON schema (the client-facing contract) rather
    than via Pydantic's internal `FieldInfo.metadata`, because the
    internal representation has changed between Pydantic minor
    versions. The JSON schema is what `/openapi.json` publishes and
    is stable across versions.
    """
    schema = PredictRequest.model_json_schema()
    features_schema = schema["properties"]["features"]
    assert features_schema.get("minItems") == EXPECTED_FEATURE_COUNT
    assert features_schema.get("maxItems") == EXPECTED_FEATURE_COUNT


def test_predict_request_rejects_wrong_feature_count():
    """The API request schema rejects too-few and too-many features."""
    with pytest.raises(pydantic.ValidationError):
        PredictRequest(features=[1.0] * (EXPECTED_FEATURE_COUNT - 1))
    with pytest.raises(pydantic.ValidationError):
        PredictRequest(features=[1.0] * (EXPECTED_FEATURE_COUNT + 1))


def test_predict_request_forbids_extra_fields():
    """The API request schema rejects unexpected top-level fields."""
    with pytest.raises(pydantic.ValidationError):
        PredictRequest(
            features=[1.0] * EXPECTED_FEATURE_COUNT, unexpected="field"
        )


def test_predict_request_accepts_valid_payload():
    """A correct 8-float payload validates without error."""
    req = PredictRequest(features=[0.0] * EXPECTED_FEATURE_COUNT)
    assert len(req.features) == EXPECTED_FEATURE_COUNT
