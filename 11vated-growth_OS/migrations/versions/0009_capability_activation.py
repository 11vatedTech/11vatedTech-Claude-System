"""Capability activation: founder decisions, canon events, market linkage.

Revision ID: 0009
Revises: 0008
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("capability_canon", sa.Column("external_summary", sa.Text()))
    op.add_column(
        "capability_canon",
        sa.Column("commercial_models", sa.JSON(), server_default="[]", nullable=False),
    )
    op.create_table(
        "capability_canon_event",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(80), server_default="CAPABILITY_CANON_CHANGED", nullable=False),
        sa.Column("payload", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(40), server_default="pending", nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_capability_canon_event_capability_id", "capability_canon_event", ["capability_id"])
    op.create_table(
        "capability_product_hypothesis",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hypothesis_type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), server_default="HYPOTHESIS", nullable=False),
    )
    op.create_index("ix_capability_product_hypothesis_capability_id", "capability_product_hypothesis", ["capability_id"])
    op.add_column("market_opportunity_thesis", sa.Column("capability_id", sa.String(64)))
    op.add_column("market_opportunity_thesis", sa.Column("selection_reasoning", sa.Text()))
    op.add_column("market_opportunity_thesis", sa.Column("discovery_source", sa.String(80)))
    op.add_column("market_opportunity_thesis", sa.Column("short_term_score", sa.Float(), server_default="0", nullable=False))
    op.add_column("market_opportunity_thesis", sa.Column("strategic_score", sa.Float(), server_default="0", nullable=False))
    op.create_index("ix_market_opportunity_thesis_capability_id", "market_opportunity_thesis", ["capability_id"])


def downgrade() -> None:
    op.drop_index("ix_market_opportunity_thesis_capability_id", table_name="market_opportunity_thesis")
    op.drop_column("market_opportunity_thesis", "strategic_score")
    op.drop_column("market_opportunity_thesis", "short_term_score")
    op.drop_column("market_opportunity_thesis", "discovery_source")
    op.drop_column("market_opportunity_thesis", "selection_reasoning")
    op.drop_column("market_opportunity_thesis", "capability_id")
    op.drop_index("ix_capability_product_hypothesis_capability_id", table_name="capability_product_hypothesis")
    op.drop_table("capability_product_hypothesis")
    op.drop_index("ix_capability_canon_event_capability_id", table_name="capability_canon_event")
    op.drop_table("capability_canon_event")
    op.drop_column("capability_canon", "commercial_models")
    op.drop_column("capability_canon", "external_summary")
