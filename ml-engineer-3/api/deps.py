"""Auth dependencies.

MVP NOTE: Backend owns the real OAuth2/JWT (layer 6). For the demo we read the
role from an `X-Role` header so the role-gating logic is real and demonstrable
without standing up the auth service. Swapping in JWT later means replacing only
this file — the endpoints already depend on `require_role(...)`.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from common.config import get_settings


def require_role(*allowed: str):
    def _dep(x_role: str | None = Header(default=None)) -> str:
        if x_role is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing X-Role header (demo auth)")
        if x_role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"role '{x_role}' not in {allowed}")
        return x_role

    return _dep


def require_reviewer():
    return require_role(*get_settings().reviewer_roles)
