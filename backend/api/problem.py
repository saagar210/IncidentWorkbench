"""Problem Details helpers for API error responses."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetails(BaseModel):
    """RFC 9457 problem details payload."""

    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    request_id: str | None = None
    trace_id: str | None = None


PROBLEM_JSON = "application/problem+json"


def problem_document(
    *,
    status: int,
    title: str,
    detail: str | None = None,
    type_: str = "about:blank",
    instance: str | None = None,
    request_id: str | None = None,
    trace_id: str | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = ProblemDetails(
        type=type_,
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        request_id=request_id,
        trace_id=trace_id,
    ).model_dump(exclude_none=True)

    if extras:
        payload.update(extras)

    return payload


def problem_response(
    *,
    status: int,
    title: str,
    detail: str | None = None,
    type_: str = "about:blank",
    instance: str | None = None,
    request_id: str | None = None,
    trace_id: str | None = None,
    extras: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = problem_document(
        status=status,
        title=title,
        detail=detail,
        type_=type_,
        instance=instance,
        request_id=request_id,
        trace_id=trace_id,
        extras=extras,
    )
    return JSONResponse(status_code=status, content=payload, media_type=PROBLEM_JSON)
