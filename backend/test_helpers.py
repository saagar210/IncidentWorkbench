"""Test helpers for authenticated API requests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from config import settings
from database import db
from security.auth import ensure_bootstrap_admin
from security.settings import CSRF_COOKIE_NAME, CSRF_HEADER_NAME

_auth_prereqs_ready = False


def _ensure_auth_prereqs() -> None:
    """Ensure auth tables and bootstrap user exist for tests."""
    global _auth_prereqs_ready
    if _auth_prereqs_ready:
        return

    db.run_migrations()
    ensure_bootstrap_admin()
    _auth_prereqs_ready = True


def login_admin(client: TestClient) -> dict[str, str]:
    """Authenticate test client as bootstrap admin and return CSRF headers."""
    _ensure_auth_prereqs()
    login_headers: dict[str, str] = {}
    existing_csrf = client.cookies.get(CSRF_COOKIE_NAME)
    if existing_csrf:
        login_headers[CSRF_HEADER_NAME] = existing_csrf

    response = client.post(
        "/auth/login",
        json={
            "username": settings.bootstrap_admin_username,
            "password": settings.bootstrap_admin_password,
        },
        headers=login_headers,
    )
    assert response.status_code == 200, response.text

    csrf_token = response.cookies.get(CSRF_COOKIE_NAME) or client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf_token is not None
    return {"X-CSRF-Token": csrf_token}
