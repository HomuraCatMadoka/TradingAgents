import os
from datetime import timedelta
from uuid import uuid4

import pytest
import jwt
from fastapi.security import HTTPAuthorizationCredentials

from core.exceptions import AuthError
from core.jwt import create_access_token, create_refresh_token, utcnow
from deps import get_current_user
from db import SessionLocal
from models import Session as SessionModel
from models import User


def test_get_current_user_success():
    with SessionLocal() as db:
        user = User(telegram_id=321, username="deps_user", last_active=utcnow())
        db.add(user)
        db.flush()

        session_id = uuid4()
        refresh_token, refresh_exp = create_refresh_token(user.id, str(session_id))
        session = SessionModel(
            id=session_id,
            user_id=user.id,
            token=refresh_token,
            expires_at=refresh_exp,
        )
        db.add(session)
        db.commit()

        access_token, _ = create_access_token(
        user_id=user.id, session_id=str(session.id), username=user.username
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)
    resolved_user = get_current_user(credentials, db)
    assert resolved_user.id == user.id


def test_get_current_user_expired_session():
    with SessionLocal() as db:
        user = User(telegram_id=654, username="expired", last_active=utcnow())
        db.add(user)
        db.flush()

        session = SessionModel(
            id=uuid4(),
            user_id=user.id,
            token="stale",
            expires_at=utcnow() - timedelta(minutes=1),
        )
        db.add(session)
        db.commit()

        access_token, _ = create_access_token(
            user_id=user.id, session_id=str(session.id), username=user.username
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)

        with pytest.raises(AuthError):
            get_current_user(credentials, db)


def test_get_current_user_missing_header():
    with SessionLocal() as db:
        with pytest.raises(AuthError):
            get_current_user(None, db)


def test_get_current_user_invalid_payload_and_user_missing():
    with SessionLocal() as db:
        bad_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")
        with pytest.raises(AuthError):
            get_current_user(bad_credentials, db)

        # Token without session_id to hit payload validation
        token_missing_session = jwt.encode(
            {"sub": 1, "type": "access"}, os.getenv("JWT_SECRET", "test_secret"), algorithm="HS256"
        )
        payload_only_user = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_missing_session)
        with pytest.raises(AuthError):
            get_current_user(payload_only_user, db)

        bad_uuid_token = jwt.encode(
            {"sub": 1, "session_id": "bad-uuid", "type": "access"},
            os.getenv("JWT_SECRET", "test_secret"),
            algorithm="HS256",
        )
        bad_uuid_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=bad_uuid_token)
        with pytest.raises(AuthError):
            get_current_user(bad_uuid_creds, db)

        # Valid session id but user missing
        session_id = uuid4()
        session = SessionModel(id=session_id, user_id=9999, token="t", expires_at=utcnow() + timedelta(minutes=5))
        db.add(session)
        db.commit()
        token = create_access_token(user_id=9999, session_id=str(session_id))[0]
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(AuthError):
            get_current_user(creds, db)
