"""Entry point for running the serving API with uvicorn."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "modelops.serving.app:create_app",
        factory=True,
        host="0.0.0.0",    # noqa: S104  # nosec B104 - required for Docker port mapping
        port=8000,
        log_level="info",
    )
