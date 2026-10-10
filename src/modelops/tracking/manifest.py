"""Generate a model manifest with checksums and metadata.

The manifest is a JSON file that pins every identity needed for
reproducible promotion and rollback:

- model artifact checksum (SHA-256)
- training data hash
- Git commit
- evaluation metrics
- dependency versions
- MLflow run ID and registered model version
"""
from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path

from mlflow.tracking import MlflowClient

from modelops.tracking.config import get_tracking_uri
from modelops.tracking.metadata import dependency_versions, hash_file


def sha256_file(path: Path | str) -> str:
    """Compute SHA-256 of a file."""
    return hash_file(path)


def get_registered_version(run_id: str, model_name: str) -> int:
    """Find the model version registered from a given run ID."""
    client = MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")
    for v in versions:
        if v.run_id == run_id:
            return int(v.version)
    raise ValueError(f"No registered version found for run {run_id}")


def build_manifest(
    model_name: str,
    registered_model_name: str,
    run_id: str,
    registered_model_version: int,
    local_artifact_path: Path | str,
    train_data_hash: str,
    test_metrics: dict,
) -> dict:
    """Build a complete model manifest dictionary.

    ``model_name`` is the local pipeline identifier (e.g. "gradient_boosting").
    ``registered_model_name`` is the MLflow registry name
    (e.g. "modelops-housing-regressor").
    """
    artifact_hash = sha256_file(local_artifact_path)
    return {
        "schema_version": "1.1.0",
        "model_name": model_name,
        "registered_model_name": registered_model_name,
        "mlflow_run_id": run_id,
        "registered_model_version": registered_model_version,
        "artifact_path": str(local_artifact_path),
        "artifact_sha256": artifact_hash,
        "train_data_hash": train_data_hash,
        "test_metrics": test_metrics,
        "dependencies": dependency_versions(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "created_at": datetime.now(UTC).isoformat(),
        "tracking_uri": get_tracking_uri(),
    }


def write_manifest(manifest: dict, output_dir: Path | str = "manifests") -> Path:
    """Write a manifest JSON file and return its path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{manifest['model_name']}-v{manifest['registered_model_version']}.json"
    )
    path = output_dir / filename
    path.write_text(json.dumps(manifest, indent=2))
    return path
