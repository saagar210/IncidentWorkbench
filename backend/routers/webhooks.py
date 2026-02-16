"""Webhook ingestion endpoints with replay protection and queue-first ack."""

from __future__ import annotations

import json

from fastapi import APIRouter, Request

from api.problem import problem_response
from database import db
from services.webhooks import normalize_payload, verify_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/{provider}", response_model=None)
async def ingest_webhook(provider: str, request: Request) -> object:
    """Store webhook receipts, dedupe by delivery ID, and enqueue for async processing."""
    delivery_id = (
        request.headers.get("X-Webhook-Delivery")
        or request.headers.get("X-GitHub-Delivery")
        or request.headers.get("X-Request-ID")
    )
    signature = (
        request.headers.get("X-Webhook-Signature")
        or request.headers.get("X-Hub-Signature-256")
        or request.headers.get("X-Signature-256")
    )

    if not delivery_id:
        return problem_response(
            status=400,
            title="Bad Request",
            detail="Missing webhook delivery identifier header.",
            type_="https://incident-workbench.dev/problems/webhook-delivery-id",
            instance=str(request.url.path),
            request_id=getattr(request.state, "request_id", None),
            trace_id=getattr(request.state, "trace_id", None),
        )

    if not signature:
        return problem_response(
            status=400,
            title="Bad Request",
            detail="Missing webhook signature header.",
            type_="https://incident-workbench.dev/problems/webhook-signature-missing",
            instance=str(request.url.path),
            request_id=getattr(request.state, "request_id", None),
            trace_id=getattr(request.state, "trace_id", None),
        )

    body = await request.body()
    signature_valid = verify_signature(provider=provider, body=body, signature=signature)
    if not signature_valid:
        return problem_response(
            status=401,
            title="Unauthorized",
            detail="Webhook signature verification failed.",
            type_="https://incident-workbench.dev/problems/webhook-signature-invalid",
            instance=str(request.url.path),
            request_id=getattr(request.state, "request_id", None),
            trace_id=getattr(request.state, "trace_id", None),
        )

    payload = normalize_payload(body)

    conn = db.get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM webhook_receipts WHERE provider = ? AND delivery_id = ?",
            (provider, delivery_id),
        ).fetchone()
        if existing:
            return {
                "status": "duplicate",
                "provider": provider,
                "delivery_id": delivery_id,
                "queued": False,
            }

        conn.execute(
            """
            INSERT INTO webhook_receipts (provider, delivery_id, signature_valid, payload)
            VALUES (?, ?, ?, ?)
            """,
            (provider, delivery_id, 1, json.dumps(payload)),
        )

        conn.execute(
            """
            INSERT INTO webhook_jobs (provider, delivery_id, payload, status)
            VALUES (?, ?, ?, 'queued')
            """,
            (provider, delivery_id, json.dumps(payload)),
        )

        conn.commit()
        return {
            "status": "accepted",
            "provider": provider,
            "delivery_id": delivery_id,
            "queued": True,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
