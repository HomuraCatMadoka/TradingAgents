import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import jwt

from core.exceptions import AuthError

JWT_ALGORITHM = "HS256"
JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY") or "dev_secret"
ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "1440"))
REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))


def utcnow() -> datetime:
    """Return timezone-aware UTC now for consistent comparisons."""
    return datetime.now(timezone.utc)


def _build_payload(
    *,
    user_id: int,
    session_id: str,
    token_type: str,
    expires_at: datetime,
    username: Optional[str] = None,
    jti: Optional[str] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {
        "sub": user_id,
        "session_id": session_id,
        "type": token_type,
        "exp": expires_at,
        "jti": jti or str(uuid4()),
    }
    if username is not None:
        payload["username"] = username
    if extra_claims:
        payload.update(extra_claims)
    return payload


def create_access_token(
    user_id: int,
    session_id: str,
    username: Optional[str] = None,
    *,
    expires_minutes: Optional[int] = None,
    secret: Optional[str] = None,
) -> Tuple[str, datetime]:
    """Create an access token and its expiry timestamp."""
    expire_at = utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRES_MINUTES if expires_minutes is None else expires_minutes
    )
    payload = _build_payload(
        user_id=user_id,
        session_id=session_id,
        token_type="access",
        expires_at=expire_at,
        username=username,
    )
    token = jwt.encode(payload, secret or JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expire_at


def create_refresh_token(
    user_id: int,
    session_id: str,
    *,
    expires_days: Optional[int] = None,
    secret: Optional[str] = None,
) -> Tuple[str, datetime]:
    """Create a refresh token and its expiry timestamp."""
    expire_at = utcnow() + timedelta(
        days=REFRESH_TOKEN_EXPIRES_DAYS if expires_days is None else expires_days
    )
    payload = _build_payload(
        user_id=user_id,
        session_id=session_id,
        token_type="refresh",
        expires_at=expire_at,
    )
    token = jwt.encode(payload, secret or JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expire_at


def verify_token(token: str, expected_type: Optional[str] = None, *, secret: Optional[str] = None) -> Dict[str, Any]:
    """Decode and validate a JWT, enforcing the expected token type when provided."""
    try:
        payload = jwt.decode(
            token,
            secret or JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_sub": False},
        )
    except jwt.ExpiredSignatureError as exc:  # type: ignore[attr-defined]
        raise AuthError("Token expired", status_code=401) from exc
    except jwt.InvalidTokenError as exc:  # type: ignore[attr-defined]
        raise AuthError("Invalid token", status_code=401) from exc

    if expected_type and payload.get("type") != expected_type:
        raise AuthError("Invalid token type", status_code=401)

    return payload
