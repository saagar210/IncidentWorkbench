"""Middleware for request ID and trace context propagation."""

from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from observability.context import set_request_id, set_trace_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request/trace correlation identifiers to request context."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        traceparent = request.headers.get("traceparent")
        tracestate = request.headers.get("tracestate")

        trace_id = None
        if traceparent:
            parts = traceparent.split("-")
            if len(parts) >= 4:
                trace_id = parts[1]

        set_request_id(request_id)
        set_trace_id(trace_id)

        request.state.request_id = request_id
        request.state.trace_id = trace_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        if traceparent:
            response.headers["traceparent"] = traceparent
        if tracestate:
            response.headers["tracestate"] = tracestate
        return response
