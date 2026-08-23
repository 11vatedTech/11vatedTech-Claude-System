"""Persistent public discovery cache and request accounting.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scout_discovery_cache",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("query_hash", sa.String(64), nullable=False),
        sa.Column("query", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("results", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_status", sa.String(40), server_default="success", nullable=False),
        sa.Column("retry_after_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_count", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("source", "query_hash", name="uq_scout_discovery_cache"),
    )
    op.create_index("ix_scout_discovery_cache_query_hash", "scout_discovery_cache", ["query_hash"])


def downgrade() -> None:
    op.drop_index("ix_scout_discovery_cache_query_hash", "scout_discovery_cache")
    op.drop_table("scout_discovery_cache")
