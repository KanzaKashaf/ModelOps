"""Serving configuration loaded from environment variables.

All fields can be overridden via environment variables prefixed with
``MODELOPS_``. For example, ``MODELOPS_MODEL_URI`` sets ``model_uri``.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServingSettings(BaseSettings):
    """Typed configuration contract for the serving application."""

    model_config = SettingsConfigDict(
        env_prefix="MODELOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    model_uri: str = Field(
        default="models:/modelops-housing-regressor@champion",
        description="MLflow model URI. Registry alias is preferred.",
    )
    model_name: str = Field(
        default="modelops-housing-regressor",
        description="Registered model name in MLflow.",
    )
    local_artifact_fallback: Path | None = Field(
        default=Path("models/gradient_boosting.joblib"),
        description="Local joblib fallback if the registry is unreachable.",
    )
    mlflow_tracking_uri: str = Field(
        default="http://127.0.0.1:5000",
        description="MLflow tracking server URI.",
    )
    max_request_bytes: int = Field(
        default=64 * 1024,
        description="Maximum allowed request body size in bytes.",
    )
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> ServingSettings:
    """Return a cached settings instance."""
    return ServingSettings()
