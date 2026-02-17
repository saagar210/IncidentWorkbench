"""Security baseline settings for auth/session/csrf behavior."""

from __future__ import annotations

import os
from typing import Literal

SESSION_COOKIE_NAME = "__Host-session"
INSECURE_SESSION_COOKIE_NAME = "workbench-session"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
SESSION_TTL_SECONDS = 60 * 60 * 8

CSRF_COOKIE_NAME = "__Host-csrf"
INSECURE_CSRF_COOKIE_NAME = "workbench-csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

DEFAULT_TRUSTED_ORIGINS = {
    "http://localhost:1420",
    "tauri://localhost",
}


def trusted_origins() -> set[str]:
    raw = os.getenv("WORKBENCH_TRUSTED_ORIGINS")
    if not raw:
        return set(DEFAULT_TRUSTED_ORIGINS)
    return {origin.strip() for origin in raw.split(",") if origin.strip()}


def cookie_secure_for_scheme(request_scheme: str) -> bool:
    """Use secure cookies on HTTPS and allow local HTTP test flows."""
    override = os.getenv("WORKBENCH_SESSION_COOKIE_SECURE")
    if override is not None:
        return override.strip().lower() in {"1", "true", "yes", "on"}
    return SESSION_COOKIE_SECURE and request_scheme.lower() == "https"


def active_cookie_names(request_scheme: str) -> tuple[str, str]:
    """Select cookie names compatible with the current scheme."""
    if cookie_secure_for_scheme(request_scheme):
        return SESSION_COOKIE_NAME, CSRF_COOKIE_NAME
    return INSECURE_SESSION_COOKIE_NAME, INSECURE_CSRF_COOKIE_NAME


def session_cookie_name_candidates() -> tuple[str, str]:
    """Cookie names accepted for session auth lookup."""
    return SESSION_COOKIE_NAME, INSECURE_SESSION_COOKIE_NAME


def csrf_cookie_name_candidates() -> tuple[str, str]:
    """Cookie names accepted for CSRF lookup."""
    return CSRF_COOKIE_NAME, INSECURE_CSRF_COOKIE_NAME
