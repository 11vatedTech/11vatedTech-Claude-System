"""Revenue Scout tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-21

Adds the Revenue Scout schema: scout control surface, market opportunity
theses, per-prospect scoring, audited acquisition transitions, website audits,
scout runs, and market learning. No existing rows are touched.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _record_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    # ScoutControl — founder-scoped control surface.
    op.create_table(
        "scout_control",
        *_record_columns(),
        sa.Column("founder_id", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("mode", sa.String(40), server_default="assist", nullable=False),
        sa.Column("kill_switch", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("daily_research_budget", sa.Integer(), server_default="100", nullable=False),
        sa.Column("daily_prospect_target", sa.Integer(), server_default="10", nullable=False),
        sa.Column("daily_outreach_cap", sa.Integer(), server_default="10", nullable=False),
        sa.Column("geographies", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("excluded_industries", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("approved_offers", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("allowed_campaign_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("research_depth", sa.String(40), server_default="standard", nullable=False),
        sa.Column("quiet_hours", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("min_revenue_score", sa.Float(), server_default="0.45", nullable=False),
        sa.Column("min_evidence_confidence", sa.Float(), server_default="0.3", nullable=False),
        sa.Column("explore_exploit", sa.Float(), server_default="0.7", nullable=False),
        sa.Column("explore_adjacent", sa.Float(), server_default="0.2", nullable=False),
        sa.Column("explore_experimental", sa.Float(), server_default="0.1", nullable=False),
        sa.Column("business_postal_address", sa.Text(), nullable=True),
        sa.Column("opt_out_email", sa.String(320), nullable=True),
        sa.UniqueConstraint("founder_id", name="uq_scout_control_founder"),
    )

    # MarketOpportunityThesis.
    op.create_table(
        "market_opportunity_thesis",
        *_record_columns(),
        sa.Column("market", sa.String(300), nullable=False),
        sa.Column("buyer", sa.String(300), nullable=True),
        sa.Column("problem", sa.Text(), nullable=True),
        sa.Column("solution", sa.Text(), nullable=True),
        sa.Column("commercial_model", sa.String(120), nullable=True),
        sa.Column("expected_deal_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("expected_deal_max", sa.Numeric(14, 2), nullable=True),
        sa.Column("sales_cycle_hypothesis", sa.String(120), nullable=True),
        sa.Column("margin_hypothesis", sa.Float(), nullable=True),
        sa.Column("competition", sa.Text(), nullable=True),
        sa.Column("proof_required", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("acquisition_difficulty", sa.Float(), nullable=True),
        sa.Column("strategic_value", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("score", sa.Float(), server_default="0", nullable=False),
        sa.Column("status", sa.String(40), server_default="hypothesis", nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("source_evidence_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.ForeignKeyConstraint(["source_evidence_id"], ["source_evidence.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_market_opportunity_thesis_market", "market_opportunity_thesis", ["market"])

    # ScoutProspectScore.
    score_cols = [
        sa.Column(c, sa.Float(), server_default="0", nullable=False)
        for c in [
            "buyer_fit",
            "problem_severity",
            "ability_to_pay",
            "authority_confidence",
            "urgency",
            "reachability",
            "expected_deal_size",
            "expected_margin",
            "delivery_confidence",
            "sales_cycle_efficiency",
            "recurring_potential",
            "repeat_potential",
            "referral_potential",
            "partnership_leverage",
            "productization_potential",
            "proof_strength",
            "strategic_value",
            "founder_capacity_cost",
            "scope_risk",
            "payment_risk",
            "competitive_pressure",
            "revenue_opportunity_score",
            "short_term_score",
            "strategic_value_score",
            "combined_priority",
            "probability",
            "confidence",
        ]
    ]
    op.create_table(
        "scout_prospect_score",
        *_record_columns(),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=False), nullable=False),
        *score_cols,
        sa.Column("expected_value_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("expected_value_max", sa.Numeric(14, 2), nullable=True),
        sa.Column("recommended_sales_motion", sa.String(200), nullable=True),
        sa.Column("recommended_next_action", sa.Text(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["prospect_id"], ["prospect.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("prospect_id", name="uq_scout_prospect_score"),
    )
    op.create_index("ix_scout_prospect_score_prospect_id", "scout_prospect_score", ["prospect_id"])

    # ProspectEvent — acquisition lifecycle audit.
    op.create_table(
        "prospect_event",
        *_record_columns(),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("from_state", sa.String(64), nullable=True),
        sa.Column("to_state", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(200), server_default="scout", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_evidence_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.ForeignKeyConstraint(["prospect_id"], ["prospect.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_evidence_id"], ["source_evidence.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_prospect_event_prospect_id", "prospect_event", ["prospect_id"])

    # WebsiteAudit.
    op.create_table(
        "website_audit",
        *_record_columns(),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(80), server_default="http_fetch", nullable=False),
        sa.Column("truth_class", sa.String(40), server_default="direct_observation", nullable=False),
        sa.Column("observations", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["prospect_id"], ["prospect.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_website_audit_company_id", "website_audit", ["company_id"])
    op.create_index("ix_website_audit_prospect_id", "website_audit", ["prospect_id"])

    # ScoutRun.
    op.create_table(
        "scout_run",
        *_record_columns(),
        sa.Column("run_type", sa.String(40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(40), server_default="running", nullable=False),
        sa.Column("summary", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_scout_run_run_type", "scout_run", ["run_type"])

    # MarketLearning.
    op.create_table(
        "market_learning",
        *_record_columns(),
        sa.Column("market", sa.String(300), nullable=True),
        sa.Column("industry", sa.String(200), nullable=True),
        sa.Column("offer", sa.String(300), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("prospect_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("outcome", sa.String(60), nullable=False),
        sa.Column("deal_size", sa.Numeric(14, 2), nullable=True),
        sa.Column("sales_cycle_days", sa.Integer(), nullable=True),
        sa.Column("margin", sa.Float(), nullable=True),
        sa.Column("loss_reason", sa.Text(), nullable=True),
        sa.Column("close_reason", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaign.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["prospect_id"], ["prospect.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_market_learning_market", "market_learning", ["market"])
    op.create_index("ix_market_learning_industry", "market_learning", ["industry"])


def downgrade() -> None:
    op.drop_index("ix_market_learning_industry", "market_learning")
    op.drop_index("ix_market_learning_market", "market_learning")
    op.drop_table("market_learning")
    op.drop_index("ix_scout_run_run_type", "scout_run")
    op.drop_table("scout_run")
    op.drop_index("ix_website_audit_prospect_id", "website_audit")
    op.drop_index("ix_website_audit_company_id", "website_audit")
    op.drop_table("website_audit")
    op.drop_index("ix_prospect_event_prospect_id", "prospect_event")
    op.drop_table("prospect_event")
    op.drop_index("ix_scout_prospect_score_prospect_id", "scout_prospect_score")
    op.drop_table("scout_prospect_score")
    op.drop_index("ix_market_opportunity_thesis_market", "market_opportunity_thesis")
    op.drop_table("market_opportunity_thesis")
    op.drop_table("scout_control")
