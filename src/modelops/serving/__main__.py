"""Entry point for running the serving API with uvicorn."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "modelops.serving.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
