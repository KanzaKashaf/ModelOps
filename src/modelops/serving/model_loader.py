"""Load the champion model from MLflow or a local fallback.

Invoked once during application startup. Attempts the MLflow
registry URI first (``models:/<name>@champion``); falls back to a
local joblib artifact if the registry is unreachable.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadedModel:
    """Container for a loaded model and its resolved metadata."""

    model: object
    model_name: str
    model_version: str
    model_uri: str
    source: str  # "mlflow_registry" or "local_fallback"


def resolve_model_version(model_uri: str, model_name: str) -> str:
    """Resolve a human-readable version string from an MLflow URI.

    - ``models:/name@alias``  -> ``alias@v<resolved_version>``
    - ``models:/name/3``      -> ``v3``
    - anything else           -> ``"unknown"``

    This is a pure-ish helper: it only reaches out to MLflow for the
    alias case, and degrades gracefully if the client call fails.
    """
    from mlflow.tracking import MlflowClient

    try:
        if "@" in model_uri:
            alias = model_uri.split("@", 1)[1]
            client = MlflowClient()
            mv = client.get_model_version_by_alias(model_name, alias)
            return f"{alias}@v{mv.version}"
        # ``models:/name/<version>`` form
        if model_uri.startswith("models:/") and model_uri.count("/") >= 2:
            version = model_uri.rsplit("/", 1)[1]
            return f"v{version}"
    except Exception as exc:  # noqa: BLE001 - any registry error -> "unknown"
        logger.debug("Could not resolve model version for %s: %s", model_uri, exc)
    return "unknown"


def load_model(
    model_uri: str,
    model_name: str,
    local_fallback: Path | None,
    tracking_uri: str,
) -> LoadedModel:
    """Load the model, preferring the MLflow registry.

    Raises ``RuntimeError`` if both the registry and the fallback fail.
    """
    mlflow.set_tracking_uri(tracking_uri)

    # --- Attempt MLflow registry load first -------------------------------
    try:
        model = mlflow.sklearn.load_model(model_uri)
        version = resolve_model_version(model_uri, model_name)
        logger.info("Loaded model from MLflow registry: %s", model_uri)
        return LoadedModel(
            model=model,
            model_name=model_name,
            model_version=version,
            model_uri=model_uri,
            source="mlflow_registry",
        )
    except Exception as exc:  # noqa: BLE001 - we want to try the fallback
        logger.warning(
            "MLflow registry load failed for %s: %s. Trying local fallback.",
            model_uri,
            exc,
        )

    # --- Fallback to local joblib artifact --------------------------------
    if local_fallback and Path(local_fallback).exists():
        try:
            model = joblib.load(local_fallback)
            logger.info("Loaded model from local fallback: %s", local_fallback)
            return LoadedModel(
                model=model,
                model_name=model_name,
                model_version="local-fallback",
                model_uri=str(local_fallback),
                source="local_fallback",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Local fallback load failed: %s", exc)

    raise RuntimeError(
        f"Could not load model from {model_uri} or fallback {local_fallback}"
    )
