from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from miniapp.backend.db import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    protocol_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    protocol_type: Mapped[str | None] = mapped_column(sa.String(50))
    added_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("timezone('utc', now())"),
        nullable=False,
    )

    user = relationship("User", back_populates="favorites")

    __table_args__ = (sa.UniqueConstraint("user_id", "protocol_name"),)
