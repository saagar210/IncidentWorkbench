"""Role-based authorization helpers."""

from __future__ import annotations


def require_role(user_roles: set[str], required: set[str]) -> None:
    """Raise if the user does not hold any required role."""
    if not required.intersection(user_roles):
        raise PermissionError("forbidden")
