from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from miniapp.backend.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(sa.BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(sa.String(255))
    first_name: Mapped[Optional[str]] = mapped_column(sa.String(255))
    last_name: Mapped[Optional[str]] = mapped_column(sa.String(255))
    language_code: Mapped[Optional[str]] = mapped_column(sa.String(10))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("timezone('utc', now())"),
        nullable=False,
    )
    last_active: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True))
    settings: Mapped[dict] = mapped_column(
        JSONB,
        server_default=sa.text("'{}'::jsonb"),
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
