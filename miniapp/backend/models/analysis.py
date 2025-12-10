from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from miniapp.backend.db import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    protocol_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    query_text: Mapped[str | None] = mapped_column(sa.Text)
    query_type: Mapped[str | None] = mapped_column(sa.String(50))
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    duration: Mapped[float | None] = mapped_column(sa.Float)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("timezone('utc', now())"),
        nullable=False,
    )
    cached: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.text("false"), nullable=False
    )

    user = relationship("User", back_populates="analysis_history")

    __table_args__ = (
        sa.Index("ix_analysis_user_created", "user_id", sa.text("created_at DESC")),
    )
