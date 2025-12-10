from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(sa.BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(sa.String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(sa.String(512))
    bio: Mapped[Optional[str]] = mapped_column(sa.Text)
    first_name: Mapped[Optional[str]] = mapped_column(sa.String(255))
    last_name: Mapped[Optional[str]] = mapped_column(sa.String(255))
    language_code: Mapped[Optional[str]] = mapped_column(sa.String(10))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_active: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True))
    settings: Mapped[dict] = mapped_column(
        sa.JSON,
        server_default=sa.text("'{}'"),
        nullable=False,
    )

    analysis_history = relationship(
        "AnalysisHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    favorites = relationship(
        "Favorite",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sessions = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    watchlist_entries = relationship(
        "Watchlist",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
