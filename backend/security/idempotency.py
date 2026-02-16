"""Idempotency key middleware for unsafe HTTP methods."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import AsyncIterator
from typing import cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.problem import problem_response
from database import db

logger = logging.getLogger(__name__)

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
MAX_STORED_RESPONSE_BYTES = 1_000_000


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Replay responses for matching `Idempotency-Key` + route + request body."""

    async def dispatch(self, request: Request, call_next):
        if request.method not in WRITE_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        body = await request.body()
        request_hash = hashlib.sha256(body).hexdigest()
        route = request.url.path

        existing = self._get_existing_record(idempotency_key, route)
        if existing is not None:
            existing_hash, response_code, response_body = existing

            if existing_hash != request_hash:
                return problem_response(
                    status=409,
                    title="Conflict",
                    detail="Idempotency-Key was reused with a different request payload.",
                    type_="https://incident-workbench.dev/problems/idempotency-conflict",
                    instance=route,
                    request_id=getattr(request.state, "request_id", None),
                    trace_id=getattr(request.state, "trace_id", None),
                )

            if response_code is not None and response_body:
                try:
                    content = json.loads(response_body)
                except json.JSONDecodeError:
                    content = {"detail": "Stored idempotent response was not valid JSON."}

                replay = Response(
                    content=json.dumps(content),
                    status_code=response_code,
                    media_type="application/json",
                )
                replay.headers["Idempotency-Replayed"] = "true"
                return replay
        else:
            self._create_pending_record(idempotency_key, route, request_hash)

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        replayable_request = Request(request.scope, receive)
        replayable_request.state.request_id = getattr(request.state, "request_id", None)
        replayable_request.state.trace_id = getattr(request.state, "trace_id", None)

        response = await call_next(replayable_request)
        captured_response, response_json = await _capture_response_body(response)

        if captured_response.status_code < 500 and response_json is not None:
            self._store_response(
                idempotency_key=idempotency_key,
                route=route,
                response_code=captured_response.status_code,
                response_body=response_json,
            )

        return captured_response

    def _get_existing_record(
        self, key: str, route: str
    ) -> tuple[str, int | None, str | None] | None:
        conn = db.get_connection()
        try:
            row = conn.execute(
                "SELECT request_hash, response_code, response_body FROM idempotency_keys WHERE key = ? AND route = ?",
                (key, route),
            ).fetchone()
            if row is None:
                return None
            return row["request_hash"], row["response_code"], row["response_body"]
        finally:
            conn.close()

    def _create_pending_record(self, key: str, route: str, request_hash: str) -> None:
        conn = db.get_connection()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO idempotency_keys (key, route, request_hash) VALUES (?, ?, ?)",
                (key, route, request_hash),
            )
            conn.commit()
        finally:
            conn.close()

    def _store_response(
        self, *, idempotency_key: str, route: str, response_code: int, response_body: str
    ) -> None:
        conn = db.get_connection()
        try:
            conn.execute(
                "UPDATE idempotency_keys SET response_code = ?, response_body = ? WHERE key = ? AND route = ?",
                (response_code, response_body, idempotency_key, route),
            )
            conn.commit()
        finally:
            conn.close()


async def _capture_response_body(response: Response) -> tuple[Response, str | None]:
    body = b""
    body_iterator = getattr(response, "body_iterator", None)
    if body_iterator is not None:
        chunks = []
        async for chunk in cast(AsyncIterator[bytes], body_iterator):
            chunks.append(chunk)
        body = b"".join(chunks)
    else:
        body = getattr(response, "body", b"")

    rebuilt = Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=response.background,
    )

    if len(body) > MAX_STORED_RESPONSE_BYTES:
        logger.info("Skipping idempotency response persistence because payload is too large")
        return rebuilt, None

    if not response.headers.get("content-type", "").startswith("application/json"):
        return rebuilt, None

    try:
        parsed = json.loads(body.decode("utf-8"))
    except Exception:
        return rebuilt, None

    return rebuilt, json.dumps(parsed)
