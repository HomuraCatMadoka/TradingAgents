import os
from datetime import timezone
from typing import Any, Dict
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import verify_telegram_webapp_data
from core.exceptions import AuthError, ValidationError
from core.jwt import create_access_token, create_refresh_token, utcnow, verify_token
from core.responses import success_response
from deps import get_current_user, get_db, security
from models import Session as SessionModel
from models import User
from schemas.user import User as UserSchema

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TelegramAuthRequest(BaseModel):
    initData: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _get_bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")


@router.post("/telegram")
def telegram_auth(request: TelegramAuthRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    bot_token = _get_bot_token()
    auth_result = verify_telegram_webapp_data(request.initData, bot_token)
    if not auth_result:
        raise AuthError("Invalid authentication", status_code=401)

    user_payload = auth_result.get("user") or {}
    telegram_id = user_payload.get("id")
    if telegram_id is None:
        raise ValidationError("telegram_id", "missing user id")

    now = utcnow()
    result = db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user and user.deleted_at is not None:
        raise AuthError("User deleted", status_code=401)

    if user:
        user.username = user_payload.get("username")
        user.first_name = user_payload.get("first_name")
        user.last_name = user_payload.get("last_name")
        user.language_code = user_payload.get("language_code")
        user.last_active = now
    else:
        user = User(
            telegram_id=telegram_id,
            username=user_payload.get("username"),
            first_name=user_payload.get("first_name"),
            last_name=user_payload.get("last_name"),
            language_code=user_payload.get("language_code"),
            last_active=now,
            settings=user_payload.get("settings") or {},
        )
        db.add(user)
        db.flush()

    session_id = uuid4()
    session_entry = SessionModel(id=session_id, user_id=user.id, token="", expires_at=now)

    refresh_token, refresh_expires = create_refresh_token(user.id, str(session_id))
    access_token, access_expires = create_access_token(
        user.id, str(session_id), user.username
    )
    session_entry.token = refresh_token
    session_entry.expires_at = refresh_expires

    db.add(session_entry)
    db.commit()
    db.refresh(user)

    return success_response(
        {
            "user": UserSchema.model_validate(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_expires_at": access_expires,
            "refresh_expires_at": refresh_expires,
            "session_id": session_id,
        }
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return success_response(UserSchema.model_validate(current_user))


@router.post("/refresh")
def refresh_token(
    request: RefreshRequest, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    payload = verify_token(request.refresh_token, expected_type="refresh")
    session_id = payload.get("session_id")
    user_id = payload.get("sub")

    if session_id is None or user_id is None:
        raise AuthError("Invalid refresh token", status_code=401)

    try:
        session_uuid = UUID(str(session_id))
    except (TypeError, ValueError) as exc:
        raise AuthError("Invalid session id", status_code=401) from exc

    session = db.get(SessionModel, session_uuid)
    session_expiry = session.expires_at if session else None
    if session_expiry and session_expiry.tzinfo is None:
        session_expiry = session_expiry.replace(tzinfo=timezone.utc)

    if not session or session_expiry is None or session_expiry <= utcnow():
        raise AuthError("Session expired or revoked", status_code=401)

    if session.token != request.refresh_token:
        raise AuthError("Session revoked", status_code=401)

    user = db.get(User, user_id)
    if not user:
        raise AuthError("User not found", status_code=401)

    access_token, access_expires = create_access_token(
        user.id, str(session.id), user.username
    )
    return success_response(
        {"access_token": access_token, "access_expires_at": access_expires, "session_id": session.id}
    )


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if credentials is None or not credentials.credentials:
        raise AuthError("Missing Authorization header", status_code=401)

    payload = verify_token(credentials.credentials, expected_type="access")
    session_id = payload.get("session_id")
    if not session_id:
        raise AuthError("Invalid token payload", status_code=401)

    try:
        session_uuid = UUID(str(session_id))
    except (TypeError, ValueError) as exc:
        raise AuthError("Invalid session id", status_code=401) from exc

    session = db.get(SessionModel, session_uuid)
    if not session:
        raise AuthError("Session expired or revoked", status_code=401)

    db.delete(session)
    db.commit()

    return success_response({"message": "Logged out", "user_id": current_user.id})
