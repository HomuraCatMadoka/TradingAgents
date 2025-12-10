from datetime import timezone
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.exceptions import AuthError
from core.jwt import utcnow, verify_token
from db import get_session
from models import Session as SessionModel
from models import User

security = HTTPBearer(auto_error=False)


def get_db():
    """Yield a DB session."""
    yield from get_session()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current user from a bearer access token."""
    if credentials is None or not credentials.credentials:
        raise AuthError("Missing Authorization header", status_code=401)

    payload = verify_token(credentials.credentials, expected_type="access")
    session_id = payload.get("session_id")
    user_id = payload.get("sub")

    if session_id is None or user_id is None:
        raise AuthError("Invalid token payload", status_code=401)

    try:
        session_uuid = UUID(str(session_id))
    except (TypeError, ValueError) as exc:
        raise AuthError("Invalid session id", status_code=401) from exc

    session = db.get(SessionModel, session_uuid)
    now = utcnow()
    if session is None:
        session_expiry = None
    elif session.expires_at and session.expires_at.tzinfo is None:
        session_expiry = session.expires_at.replace(tzinfo=timezone.utc)
    else:
        session_expiry = session.expires_at

    if not session or session_expiry is None or session_expiry <= now:
        raise AuthError("Session expired or revoked", status_code=401)

    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise AuthError("User not found", status_code=401)

    return user
