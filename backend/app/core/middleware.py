import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.audit.context import (
    clear_audit_context,
    set_current_client_ip,
    set_current_request_id,
    set_current_user_agent,
)

logger = logging.getLogger("exam_arena.access")


class RequestCorrelationAndLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches a unique correlation/request ID to every incoming HTTP request,
    stores contextual client attributes in thread-safe contextvars, and produces structured
    access logs with timing metrics.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Resolve or generate correlation request ID
        incoming_id = request.headers.get("x-request-id") or request.headers.get(
            "X-Request-ID"
        )
        request_id = incoming_id.strip() if incoming_id else str(uuid.uuid4())

        # 2. Extract Client IP and User Agent
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        user_agent = request.headers.get("user-agent", "unknown")

        # 3. Bind context variables for downstream services & audit logging
        set_current_request_id(request_id)
        set_current_client_ip(client_ip)
        set_current_user_agent(user_agent)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Attach correlation ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Avoid spamming logs for health checks
            if request.url.path != "/health":
                logger.info(
                    "HTTP %s %s status=%d duration=%.2fms ip=%s req_id=%s",
                    request.method,
                    request.url.path,
                    response.status_code,
                    duration_ms,
                    client_ip,
                    request_id,
                )

            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                "HTTP %s %s error=%s duration=%.2fms ip=%s req_id=%s",
                request.method,
                request.url.path,
                exc,
                duration_ms,
                client_ip,
                request_id,
            )
            raise
        finally:
            clear_audit_context()
