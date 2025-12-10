from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from miniapp.backend.db import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    protocol_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    alert_conditions: Mapped[dict | None] = mapped_column(JSONB)
    last_notified: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    __table_args__ = (sa.UniqueConstraint("user_id", "protocol_name"),)

    user = relationship("User", back_populates="watchlist_entries")
