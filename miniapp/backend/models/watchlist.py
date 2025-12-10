from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    protocol_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    alert_conditions: Mapped[dict | None] = mapped_column(sa.JSON)
    condition_type: Mapped[str | None] = mapped_column(sa.String(50))
    threshold: Mapped[float | None] = mapped_column(sa.Float)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.text("true"), nullable=False
    )
    alert_message: Mapped[str | None] = mapped_column(sa.String(255))
    last_notified: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint("user_id", "protocol_name"),
        sa.Index("ix_watchlist_user_active", "user_id", "is_active"),
    )

    user = relationship("User", back_populates="watchlist_entries")
