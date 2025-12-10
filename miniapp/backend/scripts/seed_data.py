import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from miniapp.backend.db import async_sessionmaker
from miniapp.backend.models import AnalysisHistory, User


async def seed_demo_data() -> None:
    async with async_sessionmaker() as session:
        now = datetime.now(timezone.utc)
        demo_users = [
            {
                "telegram_id": 999001,
                "username": "demo_user",
                "first_name": "Demo",
                "last_name": "User",
                "language_code": "en",
                "last_active": now,
                "settings": {"theme": "dark"},
            },
            {
                "telegram_id": 999002,
                "username": "alice",
                "first_name": "Alice",
                "last_name": "Trader",
                "language_code": "en",
                "last_active": now,
                "settings": {"notifications": True},
            },
        ]

        users = []
        for user_data in demo_users:
            result = await session.execute(
                select(User).where(User.telegram_id == user_data["telegram_id"])
            )
            user = result.scalar_one_or_none()
            if user:
                users.append(user)
                continue

            user = User(**user_data)
            session.add(user)
            users.append(user)

        await session.flush()

        if users:
            for user in users:
                result = await session.execute(
                    select(AnalysisHistory).where(AnalysisHistory.user_id == user.id)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    continue

                analysis = AnalysisHistory(
                    user_id=user.id,
                    protocol_name="aave-v3",
                    query_text="Demo portfolio check",
                    query_type="analyze",
                    result={
                        "summary": "Demo analysis result",
                        "decision": "HOLD",
                        "notes": "Replace with real analysis output.",
                    },
                    duration=12.5,
                    created_at=now - timedelta(minutes=5),
                    cached=False,
                )
                session.add(analysis)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
