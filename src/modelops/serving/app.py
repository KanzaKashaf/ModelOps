"""FastAPI application factory for the ModelOps serving API."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from modelops.serving.config import get_settings
from modelops.serving.middleware import RequestIDMiddleware
from modelops.serving.model_loader import load_model
from modelops.serving.schemas import (
    HealthLiveResponse,
    HealthReadyResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
)
from modelops.serving.size_limit import RequestSizeLimitMiddleware

logger = logging.getLogger(__name__)

# ── Custom Prometheus metrics ─────────────────────────────────────────
PREDICTION_TOTAL = Counter(
    "modelops_predictions_total",
    "Total number of predictions served.",
    labelnames=("model_name", "model_version"),
)
INFERENCE_DURATION = Histogram(
    "modelops_inference_duration_seconds",
    "Inference duration in seconds.",
    labelnames=("model_name",),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
MODEL_LOAD_FAILURES = Counter(
    "modelops_model_load_failures_total",
    "Total model loading failures.",
)
MODEL_INFO = Gauge(
    "modelops_model_info",
    "Model information gauge (always 1; labels carry metadata).",
    labelnames=("model_name", "model_version", "source"),
)

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
TARGET_NAME = "MedHouseValue"

CANARY_SAMPLE = np.array(
    [[8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once at startup and run a canary prediction."""
    settings = get_settings()

    app.state.model_loaded = False
    app.state.model = None
    app.state.model_info: dict = {}

    try:
        loaded = load_model(
            model_uri=settings.model_uri,
            model_name=settings.model_name,
            local_fallback=settings.local_artifact_fallback,
            tracking_uri=settings.mlflow_tracking_uri,
        )
        # Canary prediction: DataFrame with named columns, matching
        # the training-time preprocessor's column requirements.
        canary_df = pd.DataFrame(CANARY_SAMPLE, columns=FEATURE_NAMES)
        _ = loaded.model.predict(canary_df)

        app.state.model = loaded.model
        app.state.model_loaded = True
        app.state.model_info = {
            "model_name": loaded.model_name,
            "model_version": loaded.model_version,
            "model_uri": loaded.model_uri,
            "source": loaded.source,
            "loaded_at": datetime.now(UTC).isoformat(),
        }
        MODEL_INFO.labels(
            model_name=loaded.model_name,
            model_version=loaded.model_version,
            source=loaded.source,
        ).set(1)
        logger.info("Model ready: %s", app.state.model_info)
    except Exception as exc:  # noqa: BLE001
        MODEL_LOAD_FAILURES.inc()
        logger.error("Model loading failed: %s", exc)
        app.state.model_loaded = False
        app.state.model_info = {"error": str(exc)}

    yield

    # Shutdown: release references
    app.state.model = None
    app.state.model_loaded = False


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="ModelOps Serving API",
        version="1.0.0",
        description="Model-serving API for the ModelOps platform.",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)

    # Reject oversized request bodies before they are read into memory.
    # The limit comes from ServingSettings.max_request_bytes (default 64 KB).
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_bytes=settings.max_request_bytes,
    )

    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/health/live", "/health/ready"],
        inprogress_name="modelops_http_inprogress",
        inprogress_labels=False,
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    _register_routes(app)
    return app


def _register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    @app.get("/", tags=["service"])
    async def root():
        return {
            "service": "ModelOps Serving API",
            "version": "1.0.0",
            "model": app.state.model_info.get("model_name", "unknown"),
            "docs": "/docs",
        }

    @app.get("/health/live", response_model=HealthLiveResponse, tags=["health"])
    async def health_live():
        """Liveness: the process is running. Does not check the model."""
        return HealthLiveResponse()

    @app.get("/health/ready", response_model=HealthReadyResponse, tags=["health"])
    async def health_ready():
        """Readiness: the model is loaded and a canary prediction succeeded."""
        if not app.state.model_loaded:
            detail = app.state.model_info.get("error", "Model not loaded")
            return JSONResponse(
                status_code=503,
                content=HealthReadyResponse(
                    status="not_ready", model_loaded=False, detail=detail
                ).model_dump(),
            )
        return HealthReadyResponse(status="ready", model_loaded=True)

    @app.get("/v1/model/info", response_model=ModelInfoResponse, tags=["model"])
    async def model_info():
        """Return approved model metadata. Never exposes local file paths."""
        info = app.state.model_info
        if not app.state.model_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")
        return ModelInfoResponse(
            model_name=info["model_name"],
            model_version=info["model_version"],
            model_uri=info["model_uri"],
            loaded_at=info["loaded_at"],
            features=FEATURE_NAMES,
            target=TARGET_NAME,
        )

    @app.post("/v1/predict", response_model=PredictResponse, tags=["predict"])
    def predict(payload: PredictRequest, request: Request):
        """Validate input and return a prediction.

        Plain ``def`` (not ``async def``) so CPU-bound scikit-learn
        inference runs in FastAPI's threadpool and does not block the
        event loop.
        """
        if not app.state.model_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")

        df = pd.DataFrame([payload.features], columns=FEATURE_NAMES)
        start = time.perf_counter()
        try:
            prediction = float(app.state.model.predict(df)[0])
        except Exception as exc:  # noqa: BLE001
            logger.exception("Inference failed")
            raise HTTPException(status_code=500, detail="Inference failed") from exc
        elapsed = time.perf_counter() - start

        info = app.state.model_info
        PREDICTION_TOTAL.labels(
            model_name=info["model_name"], model_version=info["model_version"]
        ).inc()
        INFERENCE_DURATION.labels(model_name=info["model_name"]).observe(elapsed)

        return PredictResponse(
            request_id=request.state.request_id,
            model_name=info["model_name"],
            model_version=info["model_version"],
            prediction=prediction,
            inference_ms=round(elapsed * 1000, 3),
        )
