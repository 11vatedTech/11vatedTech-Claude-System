"""Evidence-gated qualification and capability/offer canon.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def _record_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "capability_canon",
        *_record_columns(),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("category", sa.String(120), nullable=True),
        sa.Column("delivery_form", sa.String(200), nullable=True),
        sa.Column("proof_evidence", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("maturity", sa.String(80), nullable=True),
        sa.Column("typical_customer_problem", sa.Text(), nullable=True),
        sa.Column("deliverables", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("dependencies", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("delivery_complexity", sa.Float(), nullable=True),
        sa.Column("estimated_founder_effort", sa.String(120), nullable=True),
        sa.Column("reusability", sa.Float(), nullable=True),
        sa.Column("price_range_hypothesis", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("margin_hypothesis", sa.Float(), nullable=True),
        sa.Column("recurring_potential", sa.Float(), nullable=True),
        sa.Column("white_label_potential", sa.Float(), nullable=True),
        sa.Column("enterprise_potential", sa.Float(), nullable=True),
        sa.Column("related_product_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("related_completed_work", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("limitations", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("status", sa.String(40), server_default="PROPOSED", nullable=False),
        sa.Column("entered_from", sa.String(120), server_default="founder_review", nullable=False),
        sa.Column("external_claimable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("source_evidence_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("founder_review_note", sa.Text(), nullable=True),
        sa.UniqueConstraint("name", name="uq_capability_canon_name"),
    )
    op.create_index("ix_capability_canon_name", "capability_canon", ["name"])

    op.create_table(
        "commercial_offer",
        *_record_columns(),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("buyer", sa.String(300), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("deliverable", sa.Text(), nullable=False),
        sa.Column("included_capability_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=True),
        sa.Column("scope_boundaries", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("delivery_model", sa.String(120), nullable=True),
        sa.Column("timeline_hypothesis", sa.String(120), nullable=True),
        sa.Column("price_hypothesis", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("entry_offer", sa.Text(), nullable=True),
        sa.Column("premium_offer", sa.Text(), nullable=True),
        sa.Column("recurring_component", sa.Text(), nullable=True),
        sa.Column("proof_required", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("exclusions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("risks", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("status", sa.String(40), server_default="HYPOTHESIS", nullable=False),
        sa.Column("source_evidence_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("founder_review_note", sa.Text(), nullable=True),
        sa.UniqueConstraint("name", name="uq_commercial_offer_name"),
    )
    op.create_index("ix_commercial_offer_name", "commercial_offer", ["name"])

    for name in (
        "identity_confidence",
        "problem_confidence",
        "capability_fit_confidence",
        "buyer_confidence",
        "outreach_readiness_confidence",
    ):
        op.add_column("scout_prospect_score", sa.Column(name, sa.Float(), server_default="0", nullable=False))
    op.add_column(
        "scout_prospect_score",
        sa.Column("confidence_reasoning", postgresql.JSONB(), server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("scout_prospect_score", "confidence_reasoning")
    for name in (
        "outreach_readiness_confidence",
        "buyer_confidence",
        "capability_fit_confidence",
        "problem_confidence",
        "identity_confidence",
    ):
        op.drop_column("scout_prospect_score", name)
    op.drop_index("ix_commercial_offer_name", "commercial_offer")
    op.drop_table("commercial_offer")
    op.drop_index("ix_capability_canon_name", "capability_canon")
    op.drop_table("capability_canon")
