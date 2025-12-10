"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-01-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    op.create_table(
        "analysis_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("protocol_name", sa.String(length=255), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=True),
        sa.Column("query_type", sa.String(length=50), nullable=True),
        sa.Column(
            "result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "cached",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analysis_user_created",
        "analysis_history",
        ["user_id", sa.text("created_at DESC")],
        unique=False,
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("protocol_name", sa.String(length=255), nullable=False),
        sa.Column("protocol_type", sa.String(length=50), nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "protocol_name"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("protocol_name", sa.String(length=255), nullable=False),
        sa.Column(
            "alert_conditions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("last_notified", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "protocol_name"),
    )


def downgrade() -> None:
    op.drop_table("watchlist")
    op.drop_table("sessions")
    op.drop_table("favorites")
    op.drop_index("ix_analysis_user_created", table_name="analysis_history")
    op.drop_table("analysis_history")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
