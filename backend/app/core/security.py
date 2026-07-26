"""
NextDrop – JWT Security Utilities
-----------------------------------
Provides:
  - `create_access_token()` – signs a JWT for a given subject.
  - `decode_access_token()` – validates and decodes a JWT payload.
  - `get_current_user()`    – FastAPI dependency extracting the authenticated
                              user from the Bearer token in the request header.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

# OAuth2 bearer scheme – extracts the token from the Authorization header.
bearer_scheme = HTTPBearer(auto_error=True)


# ---------------------------------------------------------------------------
# Token payload schema
# ---------------------------------------------------------------------------
class TokenPayload(BaseModel):
    sub: str          # Subject – typically the artist UUID string
    scope: str        # "artist" | "admin"
    exp: datetime


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------
def create_access_token(
    subject: str,
    scope: str = "artist",
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject:      The unique identifier to embed (e.g. artist UUID).
        scope:        Permission scope – 'artist' or 'admin'.
        expires_delta: Optional override for token lifetime.

    Returns:
        A signed JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "scope": scope,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


# ---------------------------------------------------------------------------
# Token decoding & validation
# ---------------------------------------------------------------------------
def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT, returning its typed payload.

    Raises:
        HTTPException 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        raw = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return TokenPayload(**raw)
    except JWTError:
        raise credentials_exception


# ---------------------------------------------------------------------------
# FastAPI dependency – current user
# ---------------------------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenPayload:
    """Dependency: validates the Bearer token and returns the payload.

    Inject into any route that requires authentication:
        current_user: TokenPayload = Depends(get_current_user)
    """
    return decode_access_token(credentials.credentials)


def require_admin(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Dependency: validates that the token has 'admin' scope."""
    if current_user.scope != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin scope required.",
        )
    return current_user
