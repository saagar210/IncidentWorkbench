"""Session-based authentication and RBAC dependencies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response

from config import settings
from database import db
from security.rbac import require_role
from security.settings import (
    CSRF_COOKIE_NAME,
    INSECURE_CSRF_COOKIE_NAME,
    INSECURE_SESSION_COOKIE_NAME,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE,
    SESSION_TTL_SECONDS,
    active_cookie_names,
    cookie_secure_for_scheme,
    csrf_cookie_name_candidates,
    session_cookie_name_candidates,
)


@dataclass(slots=True)
class AuthUser:
    """Authenticated user context."""

    user_id: int
    username: str
    roles: set[str]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _encode_password_hash(*, password: str, salt: bytes, iterations: int) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    encoded_salt = base64.urlsafe_b64encode(salt).decode("utf-8")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${encoded_salt}${encoded_digest}"


def hash_password(password: str, *, iterations: int = 600_000) -> str:
    salt = secrets.token_bytes(16)
    return _encode_password_hash(password=password, salt=salt, iterations=iterations)


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iteration_raw, encoded_salt, encoded_digest = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iteration_raw)
        salt = base64.urlsafe_b64decode(encoded_salt.encode("utf-8"))
    except (ValueError, TypeError):
        return False

    expected = _encode_password_hash(password=password, salt=salt, iterations=iterations)
    return hmac.compare_digest(expected, encoded_hash)


def ensure_bootstrap_admin() -> None:
    """Create a local bootstrap admin user if missing."""
    if not settings.auth_enabled:
        return

    username = settings.bootstrap_admin_username.strip()
    password = settings.bootstrap_admin_password
    if not username or not password:
        return

    conn = db.get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing is not None:
            return

        conn.execute(
            """
            INSERT INTO users (username, password_hash, roles)
            VALUES (?, ?, ?)
            """,
            (username, hash_password(password), json.dumps(["admin"])),
        )
        conn.commit()
    finally:
        conn.close()


def authenticate_credentials(username: str, password: str) -> AuthUser | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, roles FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return None

        if not verify_password(password, row["password_hash"]):
            return None

        roles = set(json.loads(row["roles"]))
        return AuthUser(user_id=row["id"], username=row["username"], roles=roles)
    finally:
        conn.close()


def create_session(*, response: Response, user_id: int, request_scheme: str) -> str:
    token = secrets.token_urlsafe(48)
    token_hash = _hash_token(token)
    csrf_token = secrets.token_urlsafe(24)
    expires_at = (_utc_now() + timedelta(seconds=SESSION_TTL_SECONDS)).isoformat()

    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (token_hash, user_id, csrf_token, expires_at),
        )
        conn.commit()
    finally:
        conn.close()

    secure_cookie = cookie_secure_for_scheme(request_scheme)
    session_cookie_name, csrf_cookie_name = active_cookie_names(request_scheme)
    response.set_cookie(
        key=session_cookie_name,
        value=token,
        secure=secure_cookie,
        httponly=SESSION_COOKIE_HTTPONLY,
        samesite=SESSION_COOKIE_SAMESITE,
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    response.set_cookie(
        key=csrf_cookie_name,
        value=csrf_token,
        secure=secure_cookie,
        httponly=False,
        samesite=SESSION_COOKIE_SAMESITE,
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    return csrf_token


def revoke_session_by_token(token: str | None) -> None:
    if not token:
        return

    token_hash = _hash_token(token)
    conn = db.get_connection()
    try:
        conn.execute(
            """
            UPDATE sessions
            SET revoked_at = ?, last_seen_at = ?
            WHERE token_hash = ? AND revoked_at IS NULL
            """,
            (_utc_now().isoformat(), _utc_now().isoformat(), token_hash),
        )
        conn.commit()
    finally:
        conn.close()


def clear_auth_cookies(*, response: Response, request_scheme: str) -> None:
    del request_scheme
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=SESSION_COOKIE_HTTPONLY,
        samesite=SESSION_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=False,
        samesite=SESSION_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=INSECURE_SESSION_COOKIE_NAME,
        path="/",
        secure=False,
        httponly=SESSION_COOKIE_HTTPONLY,
        samesite=SESSION_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=INSECURE_CSRF_COOKIE_NAME,
        path="/",
        secure=False,
        httponly=False,
        samesite=SESSION_COOKIE_SAMESITE,
    )


def session_token_from_request(request: Request) -> str | None:
    for cookie_name in session_cookie_name_candidates():
        token = request.cookies.get(cookie_name)
        if token:
            return token
    return None


def csrf_token_from_request(request: Request) -> str | None:
    for cookie_name in csrf_cookie_name_candidates():
        token = request.cookies.get(cookie_name)
        if token:
            return token
    return None


def get_current_user(request: Request) -> AuthUser:
    if not settings.auth_enabled:
        return AuthUser(user_id=0, username="auth-disabled", roles={"admin"})

    token = session_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    token_hash = _hash_token(token)

    conn = db.get_connection()
    try:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.roles, s.expires_at
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.revoked_at IS NULL
            """,
            (token_hash,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=401, detail="Invalid session")

        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at < _utc_now():
            conn.execute(
                "UPDATE sessions SET revoked_at = ? WHERE token_hash = ?",
                (_utc_now().isoformat(), token_hash),
            )
            conn.commit()
            raise HTTPException(status_code=401, detail="Session expired")

        conn.execute(
            "UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
            (_utc_now().isoformat(), token_hash),
        )
        conn.commit()

        roles = set(json.loads(row["roles"]))
        return AuthUser(user_id=row["id"], username=row["username"], roles=roles)
    finally:
        conn.close()


def require_roles_dependency(required: set[str]):
    def dependency(current_user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
        try:
            require_role(current_user.roles, required)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Forbidden") from exc
        return current_user

    return dependency
