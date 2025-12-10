import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/miniapp"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
ECHO_SQL = os.getenv("SQL_ECHO", "0") == "1"


class Base(DeclarativeBase):
    """Base class for all models."""


engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=ECHO_SQL)
async_sessionmaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async session."""
    async with async_sessionmaker() as session:
        yield session


async def close_engine() -> None:
    """Dispose the engine, used on application shutdown."""
    await engine.dispose()
