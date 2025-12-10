import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import verify_telegram_webapp_data
from db import close_engine, get_session
from models import Session as SessionModel
from models import User
from schemas import User as UserSchema

# Load env from repo root and local directory (if present)
ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN", "your_bot_token_here")
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("JWT_SECRET_KEY", "dev_secret"))
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_engine()


app = FastAPI(title="DeFi Agent API", lifespan=lifespan)

# Allow frontends (Telegram WebView + local dev) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "message": "DeFi Agent API is running"}


@app.get("/api/protocols")
async def get_protocols() -> Dict[str, List[Dict[str, Any]]]:
    # Placeholder data for frontend integration; replace with live query once data source is wired.
    return {
        "data": [
            {"name": "Aave V3", "tvl": 5_234_567_890, "apy": 3.5},
            {"name": "Uniswap V3", "tvl": 4_123_456_789, "apy": 12.8},
            {"name": "Compound V3", "tvl": 2_345_678_901, "apy": 4.2},
        ]
    }


class AuthRequest(BaseModel):
    initData: str


@app.post("/api/auth/telegram")
async def telegram_auth(
    request: AuthRequest, db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    auth_result = verify_telegram_webapp_data(request.initData, BOT_TOKEN)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication"
        )

    user_payload = auth_result.get("user", {})
    telegram_id = user_payload.get("id")
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing telegram user id",
        )

    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(minutes=JWT_EXPIRES_MINUTES)

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

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
        await db.flush()

    payload = {
        "sub": telegram_id,
        "username": user_payload.get("username"),
        "exp": expires_at,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    session_entry = SessionModel(user_id=user.id, token=token, expires_at=expires_at)
    db.add(session_entry)
    await db.commit()
    await db.refresh(user)

    return {"user": UserSchema.model_validate(user), "token": token, "expires_at": expires_at}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
