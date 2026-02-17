"""Authentication router for session login/logout and user context."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from models.api import AuthSessionResponse, AuthUserResponse, LoginRequest
from security.auth import (
    AuthUser,
    authenticate_credentials,
    clear_auth_cookies,
    create_session,
    get_current_user,
    revoke_session_by_token,
    session_token_from_request,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginRequest, request: Request, response: Response) -> AuthSessionResponse:
    """Authenticate with username/password and issue session + csrf cookies."""
    user = authenticate_credentials(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    csrf_token = create_session(
        response=response, user_id=user.user_id, request_scheme=request.url.scheme
    )
    return AuthSessionResponse(
        user=AuthUserResponse(username=user.username, roles=sorted(user.roles)),
        csrf_token=csrf_token,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, str]:
    """Revoke the current session and clear auth cookies."""
    del current_user
    session_token = session_token_from_request(request)
    revoke_session_by_token(session_token)
    clear_auth_cookies(response=response, request_scheme=request.url.scheme)
    return {"status": "logged_out"}


@router.get("/me")
async def me(current_user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUserResponse:
    """Return the authenticated user context."""
    return AuthUserResponse(username=current_user.username, roles=sorted(current_user.roles))
