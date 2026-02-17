"""Webhook verification and queueing helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from config import settings


def secret_for_provider(provider: str) -> str:
    env_key = f"WORKBENCH_WEBHOOK_SECRET_{provider.upper()}"
    return os.getenv(env_key, os.getenv("WORKBENCH_WEBHOOK_SECRET", settings.webhook_secret))


def verify_signature(*, provider: str, body: bytes, signature: str) -> bool:
    secret = secret_for_provider(provider)
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    candidate = signature.strip()
    if candidate.startswith("sha256="):
        candidate = candidate.split("=", maxsplit=1)[1]

    return hmac.compare_digest(candidate, expected)


def normalize_payload(body: bytes) -> dict[str, Any]:
    decoded = body.decode("utf-8")
    parsed = json.loads(decoded)
    if isinstance(parsed, dict):
        return parsed
    return {"data": parsed}
