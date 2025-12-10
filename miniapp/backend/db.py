import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/miniapp"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
ECHO_SQL = os.getenv("SQL_ECHO", "0") == "1"


class Base(DeclarativeBase):
    """Base class for all models."""


engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""), echo=ECHO_SQL, future=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a sync session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def close_engine() -> None:
    """Dispose the engine, used on application shutdown."""
    engine.dispose()
