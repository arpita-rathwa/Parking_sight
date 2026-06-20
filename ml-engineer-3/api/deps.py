"""Auth dependencies — JWT verification.

Swapped from demo X-Role header to real JWT verification using the shared
backend auth scheme. Relies on JWT_SECRET_KEY env var set in the service.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from common.config import get_settings

_bearer = HTTPBearer(auto_error=False)


def require_role(*allowed: str):
    def _dep(
        creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> str:
        if creds is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authorization header")
        settings = get_settings()
        try:
            payload = jwt.decode(
                creds.credentials,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

        role: str = payload.get("role", "")
        if role not in allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Role '{role}' not in {allowed}",
            )
        return role

    return _dep


def require_reviewer():
    return require_role(*get_settings().reviewer_roles)
