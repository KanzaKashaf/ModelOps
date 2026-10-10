"""MLflow tracking configuration.

Centralises the tracking URI so every module uses the same server.
"""
from __future__ import annotations

import os

DEFAULT_TRACKING_URI = "http://127.0.0.1:5000"
EXPERIMENT_NAME = "modelops-housing"


def get_tracking_uri() -> str:
    """Return the MLflow tracking URI from environment or default."""
    return os.environ.get("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI)


def set_tracking_uri() -> None:
    """Set the MLflow tracking URI globally for the current process."""
    import mlflow

    mlflow.set_tracking_uri(get_tracking_uri())


def ensure_experiment() -> str:
    """Create the experiment if it does not exist; return its experiment_id."""
    import mlflow

    set_tracking_uri()
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
    else:
        experiment_id = experiment.experiment_id
    mlflow.set_experiment(EXPERIMENT_NAME)
    return experiment_id
