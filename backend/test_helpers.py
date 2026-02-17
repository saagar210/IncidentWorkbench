"""Test helpers for authenticated API requests."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from database import db
from security.auth import ensure_bootstrap_admin, hash_password
from security.settings import CSRF_HEADER_NAME, csrf_cookie_name_candidates

_auth_prereqs_ready = False
TEST_ADMIN_USERNAME = "test-admin"
TEST_ADMIN_PASSWORD = "test-only-password"


def _first_cookie_value(client: TestClient, names: tuple[str, ...]) -> str | None:
    for name in names:
        value = client.cookies.get(name)
        if value:
            return value
    return None


def _ensure_auth_prereqs() -> None:
    """Ensure auth tables and bootstrap user exist for tests."""
    global _auth_prereqs_ready
    if _auth_prereqs_ready:
        return

    db.run_migrations()
    ensure_bootstrap_admin()
    _seed_test_admin()
    _auth_prereqs_ready = True


def _seed_test_admin() -> None:
    """Ensure deterministic admin credentials exist for tests."""
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (TEST_ADMIN_USERNAME,),
        ).fetchone()
        password_hash = hash_password(TEST_ADMIN_PASSWORD)
        roles = json.dumps(["admin"])
        if row is None:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, roles)
                VALUES (?, ?, ?)
                """,
                (TEST_ADMIN_USERNAME, password_hash, roles),
            )
        else:
            conn.execute(
                """
                UPDATE users
                SET password_hash = ?, roles = ?
                WHERE id = ?
                """,
                (password_hash, roles, row["id"]),
            )
        conn.commit()
    finally:
        conn.close()


def login_admin(client: TestClient) -> dict[str, str]:
    """Authenticate test client as bootstrap admin and return CSRF headers."""
    _ensure_auth_prereqs()
    login_headers: dict[str, str] = {}
    existing_csrf = _first_cookie_value(client, csrf_cookie_name_candidates())
    if existing_csrf:
        login_headers[CSRF_HEADER_NAME] = existing_csrf

    response = client.post(
        "/auth/login",
        json={
            "username": TEST_ADMIN_USERNAME,
            "password": TEST_ADMIN_PASSWORD,
        },
        headers=login_headers,
    )
    assert response.status_code == 200, response.text

    csrf_token = _first_cookie_value(client, csrf_cookie_name_candidates())
    if csrf_token is None:
        for name in csrf_cookie_name_candidates():
            cookie = response.cookies.get(name)
            if cookie:
                csrf_token = cookie
                break
    assert csrf_token is not None
    return {"X-CSRF-Token": csrf_token}
