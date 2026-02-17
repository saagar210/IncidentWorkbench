"""CSRF middleware for browser session requests."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from api.problem import problem_response
from security.settings import (
    CSRF_HEADER_NAME,
    csrf_cookie_name_candidates,
    session_cookie_name_candidates,
    trusted_origins,
)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Require CSRF token validation for state-changing browser requests."""

    async def dispatch(self, request: Request, call_next):
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # Only enforce CSRF when a browser session cookie is present.
        session_cookie_present = any(
            request.cookies.get(cookie_name) for cookie_name in session_cookie_name_candidates()
        )
        if not session_cookie_present:
            return await call_next(request)

        origin = request.headers.get("origin")
        if origin and origin not in trusted_origins():
            return problem_response(
                status=403,
                title="Forbidden",
                detail="Origin is not allowed for this session.",
                type_="https://incident-workbench.dev/problems/csrf-origin",
                instance=str(request.url.path),
                request_id=getattr(request.state, "request_id", None),
                trace_id=getattr(request.state, "trace_id", None),
            )

        csrf_cookie = next(
            (
                request.cookies.get(cookie_name)
                for cookie_name in csrf_cookie_name_candidates()
                if request.cookies.get(cookie_name)
            ),
            None,
        )
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return problem_response(
                status=403,
                title="Forbidden",
                detail="CSRF token missing or invalid.",
                type_="https://incident-workbench.dev/problems/csrf-token",
                instance=str(request.url.path),
                request_id=getattr(request.state, "request_id", None),
                trace_id=getattr(request.state, "trace_id", None),
            )

        return await call_next(request)
