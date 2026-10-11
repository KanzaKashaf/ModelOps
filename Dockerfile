# syntax=docker/dockerfile:1.7

# ══════════════════════════════════════════════════════════════════
# Stage 1: Builder — install dependencies with uv
# ══════════════════════════════════════════════════════════════════
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS builder

# Copy the uv binary from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation for faster cold starts.
# Copy mode makes the venv portable between build stages.
# UV_NO_DEV=1 excludes dev dependencies from the production image.
# UV_HTTP_TIMEOUT raised from default 30s: large packages (scipy,
# pyarrow, numpy) exceed the default on slow or remote links.
# UV_CONCURRENT_DOWNLOADS=1 serialises downloads, avoiding contention
# on bandwidth-limited connections.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_PREFERENCE=system \
    UV_HTTP_TIMEOUT=900 \
    UV_HTTP_RETRIES=5 \
    UV_CONCURRENT_DOWNLOADS=1

# Install dependencies in a separate layer for caching.
# The lockfile and pyproject.toml are copied first so that a
# source-code change does not invalidate the dependency layer.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy application source and install the project itself.
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# ══════════════════════════════════════════════════════════════════
# Stage 2: Runtime — minimal image, non-root user
# ══════════════════════════════════════════════════════════════════
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS runtime

# Install only runtime system dependencies.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with a fixed UID/GID.
# Fixed UID ensures consistency with Kubernetes SecurityContext
# (runAsUser: 1001) in Phase 7.
# --no-create-home: reduces attack surface (no ~/.bashrc, ~/.ssh).
# --shell /usr/sbin/nologin: prevents interactive login.
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup \
        --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Copy the virtual environment and application from the builder.
COPY --from=builder --chown=1001:1001 /app/.venv /app/.venv
COPY --from=builder --chown=1001:1001 /app/src /app/src

# Copy the entrypoint script.
COPY --chown=1001:1001 docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Activate the virtual environment.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to the non-root user.
USER 1001

# Expose only the application port.
EXPOSE 8000

# Health check: the container is healthy if the liveness endpoint responds.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health/live || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "modelops.serving"]