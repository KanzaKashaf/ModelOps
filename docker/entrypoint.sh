#!/usr/bin/env bash
set -euo pipefail

# Wait for MLflow to become available if a tracking URI is set.
# This handles Compose dependency ordering even if the health check
# is too lenient, and it prevents a startup race when the serving
# container is faster than MLflow.
if [ -n "${MODELOPS_MLFLOW_TRACKING_URI:-}" ]; then
    echo "Waiting for MLflow at ${MODELOPS_MLFLOW_TRACKING_URI}..."
    for i in $(seq 1 30); do
        if curl -sf "${MODELOPS_MLFLOW_TRACKING_URI}/health" > /dev/null 2>&1; then
            echo "MLflow is ready."
            break
        fi
        echo "  attempt ${i}/30..."
        sleep 2
    done
fi

# Execute the CMD (default: python -m modelops.serving).
exec "$@"
