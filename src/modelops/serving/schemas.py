"""Versioned request and response schemas for the serving API.

Each schema is tied to the ``/v1/`` URL prefix. If the feature
signature changes in a future phase, introduce ``/v2/`` with new
schemas rather than mutating these, so existing clients keep working.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """V1 prediction request.

    The feature vector must match the training-time feature signature
    exactly and in order:

        MedInc, HouseAge, AveRooms, AveBedrms,
        Population, AveOccup, Latitude, Longitude
    """

    model_config = ConfigDict(extra="forbid")

    features: list[float] = Field(
        ...,
        min_length=8,
        max_length=8,
        description="Feature vector in training order (exactly 8 values).",
    )


class PredictResponse(BaseModel):
    """V1 prediction response."""

    request_id: str = Field(..., description="Unique request identifier.")
    model_name: str = Field(..., description="Registered model name.")
    model_version: str = Field(..., description="Resolved model version or alias.")
    prediction: float = Field(..., description="Predicted median house value.")
    inference_ms: float = Field(
        ..., description="Server-side inference duration in milliseconds."
    )


class ModelInfoResponse(BaseModel):
    """Model metadata response.

    Never exposes local file paths; ``model_uri`` is the governed
    MLflow registry URI.
    """

    model_name: str
    model_version: str
    model_uri: str
    loaded_at: str = Field(
        ..., description="ISO 8601 UTC timestamp when the model was loaded."
    )
    features: list[str] = Field(..., description="Expected feature names in order.")
    target: str = Field(..., description="Target column name.")


class HealthLiveResponse(BaseModel):
    """Liveness response."""

    status: Literal["alive"] = "alive"


class HealthReadyResponse(BaseModel):
    """Readiness response."""

    status: Literal["ready", "not_ready"]
    model_loaded: bool
    detail: str | None = None
