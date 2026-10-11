"""Request ID middleware for correlation and logging.

Every request receives a unique ID. If the client supplies an
``X-Request-ID`` header, that value is honoured; otherwise a new UUID4
is generated. The ID is:
- stored in ``request.state.request_id`` for handlers to read,
- returned in the ``X-Request-ID`` response header,
- available for logging and metric label correlation.
"""
from __future__ import annotations

import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request and response."""

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers[self.HEADER_NAME] = request_id
        return response
