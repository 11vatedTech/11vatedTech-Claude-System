"""Capability Intelligence persistence.

Revision ID: 0007
Revises: 0006
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def _base(name: str) -> list:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table("trusted_repository_root", *_base("trusted_repository_root"),
        sa.Column("path", sa.String(2048), nullable=False), sa.Column("label", sa.String(200)),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("founder_id", sa.String(64), server_default="founder", nullable=False),
        sa.Column("last_scan_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.UniqueConstraint("path", name="uq_trusted_repository_root_path"))
    op.create_table("project_evidence_record", *_base("project_evidence_record"),
        sa.Column("repository_root_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("trusted_repository_root.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False), sa.Column("path", sa.String(2048), nullable=False),
        sa.Column("git_branch", sa.String(200)), sa.Column("git_status", sa.String(120)), sa.Column("remote_url", sa.String(2048)),
        sa.Column("readme_summary", sa.Text()), sa.Column("languages", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("manifests", postgresql.JSONB(), server_default="[]", nullable=False), sa.Column("source_directories", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("test_summary", sa.Text()), sa.Column("artifact_paths", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("evidence_hash", sa.String(64), nullable=False), sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intelligence_profile", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("privacy_notes", sa.Text(), server_default="Source remains local; only summaries and hashes persist.", nullable=False),
        sa.UniqueConstraint("path", name="uq_project_evidence_path"))
    op.create_table("capability_evidence_record", *_base("capability_evidence_record"),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("project_evidence_record.id", ondelete="SET NULL")),
        sa.Column("source_type", sa.String(80), nullable=False), sa.Column("source_location", sa.String(2048), nullable=False),
        sa.Column("artifact", sa.String(500)), sa.Column("category", sa.String(80), server_default="DOCUMENTED_CLAIM", nullable=False), sa.Column("summary", sa.Text(), nullable=False), sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("sensitivity", sa.String(40), server_default="INTERNAL", nullable=False), sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False), sa.Column("private", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.create_table("capability_review_event", *_base("capability_review_event"),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_state", sa.String(60)), sa.Column("new_state", sa.String(60), nullable=False),
        sa.Column("changed_fields", postgresql.JSONB(), server_default="{}", nullable=False), sa.Column("action", sa.String(80), nullable=False),
        sa.Column("reason", sa.Text()), sa.Column("evidence_context", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("actor", sa.String(120), server_default="founder", nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("problem_canon", *_base("problem_canon"),
        sa.Column("name", sa.String(300), nullable=False), sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("source_prospect_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("prospect.id", ondelete="SET NULL")),
        sa.Column("evidence_ids", postgresql.JSONB(), server_default="[]", nullable=False), sa.Column("status", sa.String(40), server_default="hypothesis", nullable=False),
        sa.UniqueConstraint("name", name="uq_problem_canon_name"))
    op.create_table("problem_capability_match", *_base("problem_capability_match"),
        sa.Column("problem_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("problem_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fit_confidence", sa.Float(), server_default="0", nullable=False), sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("delivery_complexity", sa.Float()), sa.Column("founder_effort", sa.String(120)), sa.Column("reuse_potential", sa.Float()),
        sa.Column("limitations", postgresql.JSONB(), server_default="[]", nullable=False), sa.Column("commercial_suitability", sa.Float()),
        sa.UniqueConstraint("problem_id", "capability_id", name="uq_problem_capability_match"))
    op.create_table("capability_gap", *_base("capability_gap"),
        sa.Column("problem_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("problem_canon.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(300), nullable=False), sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("sample_size", sa.Integer(), server_default="1", nullable=False), sa.Column("recommended_action", sa.String(40), server_default="REVIEW", nullable=False),
        sa.Column("status", sa.String(40), server_default="PROPOSED", nullable=False))
    op.create_table("capability_demand_signal", *_base("capability_demand_signal"),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="SET NULL")),
        sa.Column("problem_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("problem_canon.id", ondelete="SET NULL")),
        sa.Column("sample_size", sa.Integer(), server_default="0", nullable=False), sa.Column("observed_demand", sa.Integer(), server_default="0", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False), sa.Column("explanation", sa.Text(), nullable=False))
    op.create_table("capability_portfolio_snapshot", *_base("capability_portfolio_snapshot"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("verified_capability_ids", postgresql.JSONB(), server_default="[]", nullable=False), sa.Column("proposed_capability_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("demand_summary", postgresql.JSONB(), server_default="{}", nullable=False), sa.Column("private_source_count", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    for table in ("capability_portfolio_snapshot", "capability_demand_signal", "capability_gap", "problem_capability_match", "problem_canon", "capability_review_event", "capability_evidence_record", "project_evidence_record", "trusted_repository_root"):
        op.drop_table(table)
