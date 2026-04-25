"""
Structured request logging middleware.

Every request gets:
  - A short UUID (request_id) injected into request.state and response header
  - A JSON log line: method, path, status, latency, request_id
  - Errors are logged with full traceback at ERROR level

This makes every bug traceable end-to-end:
  1. User reports error — they have the request_id from the response header
  2. Search logs for that request_id — find the exact failed request + traceback
"""
import time
import uuid
import logging

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger("physics_blog")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            ms = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "unhandled_exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                ms=ms,
                error=str(exc),
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error.", "request_id": request_id},
            )

        ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=ms,
            ip=request.client.host if request.client else "unknown",
        )
        response.headers["X-Request-ID"] = request_id
        return response