#!/usr/bin/env bash
# Build the serving image with an immutable commit-SHA tag and OCI labels.
set -euo pipefail

GIT_SHA=$(git rev-parse --short HEAD)
GIT_SHA_FULL=$(git rev-parse HEAD)
IMAGE_NAME="modelops-serving"

echo "Building ${IMAGE_NAME}:${GIT_SHA} (${GIT_SHA_FULL})"

# Optional UV_INDEX_URL override for slow networks. Not committed; pass
# via env var or build-arg if your network requires a regional mirror.
BUILD_ARGS=()
if [ -n "${UV_INDEX_URL:-}" ]; then
    BUILD_ARGS+=("--build-arg" "UV_INDEX_URL=${UV_INDEX_URL}")
fi

docker build \
    "${BUILD_ARGS[@]}" \
    --label "org.opencontainers.image.revision=${GIT_SHA_FULL}" \
    --label "org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --label "org.opencontainers.image.source=https://github.com/KanzaKashaf/ModelOps" \
    --label "org.opencontainers.image.title=modelops-serving" \
    -t "${IMAGE_NAME}:${GIT_SHA}" \
    -t "${IMAGE_NAME}:latest" \
    .

echo "Built ${IMAGE_NAME}:${GIT_SHA}"
echo "Full SHA: ${GIT_SHA_FULL}"
