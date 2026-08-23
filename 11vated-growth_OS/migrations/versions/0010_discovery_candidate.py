"""Discovery candidate layer: pre-prospect entities, source effectiveness.

Revision ID: 0010
Revises: 0009
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def _uuid() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True)


def upgrade() -> None:
    op.create_table(
        "discovery_candidate",
        _uuid(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("source_identity_key", sa.String(320), nullable=False),
        sa.Column("source_evidence_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("source_evidence.id", ondelete="SET NULL")),
        sa.Column("legacy_prospect_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("prospect.id", ondelete="SET NULL")),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("prospect.id", ondelete="SET NULL")),
        sa.Column("canonical_name", sa.String(300), nullable=False),
        sa.Column("state", sa.String(64), server_default="discovered_signal", nullable=False),
        sa.Column("entity_type", sa.String(64), server_default="unknown", nullable=False),
        sa.Column("commercial_status", sa.String(64), server_default="commercial_unverified", nullable=False),
        sa.Column("activity_status", sa.String(64), server_default="unknown", nullable=False),
        sa.Column("need_evidence_class", sa.String(64), server_default="no_need_evidence", nullable=False),
        sa.Column("purchasing_capacity", sa.String(64), server_default="unknown", nullable=False),
        sa.Column("track", sa.String(64), server_default="not_commercial", nullable=False),
        sa.Column("official_website", sa.String(2048)),
        sa.Column("country_region", sa.String(300)),
        sa.Column("identity_confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("commercial_entity_confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("market_fit_confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("buyer_potential_confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("discovery_priority_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("problem_evidence", sa.Text()),
        sa.Column("products_projects", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("public_source_refs", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("decision_maker_evidence", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("contact_paths", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("external_ids", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("enrichment", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("qualification_outcome", sa.String(200)),
        sa.Column("last_verified_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("source", "source_identity_key", name="uq_discovery_candidate_source_identity"),
    )
    op.create_index("ix_discovery_candidate_source", "discovery_candidate", ["source"])
    op.create_index("ix_discovery_candidate_canonical_name", "discovery_candidate", ["canonical_name"])
    op.create_index("ix_discovery_candidate_state", "discovery_candidate", ["state"])
    op.create_index("ix_discovery_candidate_source_evidence_id", "discovery_candidate", ["source_evidence_id"])
    op.create_index("ix_discovery_candidate_legacy_prospect_id", "discovery_candidate", ["legacy_prospect_id"])
    op.create_index("ix_discovery_candidate_prospect_id", "discovery_candidate", ["prospect_id"])

    op.create_table(
        "discovery_candidate_event",
        _uuid(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("discovery_candidate.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state", sa.String(64)),
        sa.Column("to_state", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(200), server_default="scout", nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_evidence_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("source_evidence.id", ondelete="SET NULL")),
    )
    op.create_index("ix_discovery_candidate_event_candidate_id", "discovery_candidate_event", ["candidate_id"])

    op.create_table(
        "source_effectiveness",
        _uuid(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("market", sa.String(300)),
        sa.Column("candidates_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("verified_commercial_entities", sa.Integer(), server_default="0", nullable=False),
        sa.Column("problem_signals", sa.Integer(), server_default="0", nullable=False),
        sa.Column("capability_matches", sa.Integer(), server_default="0", nullable=False),
        sa.Column("verified_contacts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sales_qualified", sa.Integer(), server_default="0", nullable=False),
        sa.Column("promoted_to_prospect", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicate_rate", sa.Float(), server_default="0", nullable=False),
        sa.Column("false_positive_rate", sa.Float(), server_default="0", nullable=False),
        sa.Column("verified_entity_rate", sa.Float(), server_default="0", nullable=False),
        sa.Column("problem_signal_rate", sa.Float(), server_default="0", nullable=False),
        sa.Column("recommendation", sa.Text()),
        sa.Column("notes", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source", "market", name="uq_source_effectiveness_source_market"),
    )
    op.create_index("ix_source_effectiveness_source", "source_effectiveness", ["source"])
    op.create_index("ix_source_effectiveness_market", "source_effectiveness", ["market"])


def downgrade() -> None:
    op.drop_index("ix_source_effectiveness_market", table_name="source_effectiveness")
    op.drop_index("ix_source_effectiveness_source", table_name="source_effectiveness")
    op.drop_table("source_effectiveness")
    op.drop_index("ix_discovery_candidate_event_candidate_id", table_name="discovery_candidate_event")
    op.drop_table("discovery_candidate_event")
    for idx in (
        "ix_discovery_candidate_source",
        "ix_discovery_candidate_canonical_name",
        "ix_discovery_candidate_state",
        "ix_discovery_candidate_source_evidence_id",
        "ix_discovery_candidate_legacy_prospect_id",
        "ix_discovery_candidate_prospect_id",
    ):
        op.drop_index(idx, table_name="discovery_candidate")
    op.drop_table("discovery_candidate")
