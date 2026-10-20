"""Request size limiting middleware.

Rejects requests whose Content-Length header exceeds a configurable
maximum. This prevents memory exhaustion from oversized prediction
payloads. The limit is enforced before the request body is read.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

DEFAULT_MAX_BYTES = 64 * 1024  # 64 KB


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds ``max_bytes``."""

    def __init__(self, app, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )
            if length > self.max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"Request body too large. "
                            f"Maximum allowed: {self.max_bytes} bytes."
                        )
                    },
                )

        # If Content-Length is missing, check the actual body size
        # (urllib.request doesn't send Content-Length for bytes bodies)
        try:
            body = await request.body()
            if len(body) > self.max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"Request body too large. "
                            f"Maximum allowed: {self.max_bytes} bytes."
                        )
                    },
                )
            # Re-inject the body so the route handler can read it
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
        except Exception:
            pass # Let the normal error handling deal with it

        return await call_next(request)
