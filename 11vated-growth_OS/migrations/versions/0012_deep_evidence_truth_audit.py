"""Add deep evidence truth audit fields: provenance, sufficiency, machine recommendations.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

from growthos.domain.base import jsonb

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- capability_evidence_record: provenance + sufficiency ---
    op.add_column("capability_evidence_record", sa.Column("branch", sa.String(200), nullable=True))
    op.add_column("capability_evidence_record", sa.Column("commit_sha", sa.String(40), nullable=True))
    op.add_column("capability_evidence_record", sa.Column("evidence_source", sa.String(40), server_default="github", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("files_discovered", sa.Integer, server_default="0", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("files_inspected", sa.Integer, server_default="0", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("source_files_inspected", sa.Integer, server_default="0", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("test_files_inspected", sa.Integer, server_default="0", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("build_files_inspected", sa.Integer, server_default="0", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("docs_inspected", sa.Integer, server_default="0", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("deep_review_status", sa.String(40), server_default="NOT_REVIEWED", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("coverage_limitations", jsonb, nullable=False, server_default="[]"))
    op.add_column("capability_evidence_record", sa.Column("test_quality", sa.String(60), nullable=True))
    op.add_column("capability_evidence_record", sa.Column("build_quality", sa.String(60), nullable=True))
    op.add_column("capability_evidence_record", sa.Column("runtime_quality", sa.String(60), nullable=True))
    op.add_column("capability_evidence_record", sa.Column("evidence_independence", sa.String(60), nullable=True))
    op.add_column("capability_evidence_record", sa.Column("implementation_details", jsonb, nullable=False, server_default="{}"))

    # --- capability_canon: machine recommendation ---
    op.add_column("capability_canon", sa.Column("recommended_decision", sa.String(60), nullable=True))
    op.add_column("capability_canon", sa.Column("recommendation_reason", sa.Text, nullable=True))
    op.add_column("capability_canon", sa.Column("recommendation_confidence", sa.Float, nullable=True))
    op.add_column("capability_canon", sa.Column("evidence_summary_for_review", jsonb, nullable=False, server_default="{}"))
    op.add_column("capability_canon", sa.Column("deep_review_completeness", jsonb, nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("capability_canon", "deep_review_completeness")
    op.drop_column("capability_canon", "evidence_summary_for_review")
    op.drop_column("capability_canon", "recommendation_confidence")
    op.drop_column("capability_canon", "recommendation_reason")
    op.drop_column("capability_canon", "recommended_decision")
    op.drop_column("capability_evidence_record", "implementation_details")
    op.drop_column("capability_evidence_record", "evidence_independence")
    op.drop_column("capability_evidence_record", "runtime_quality")
    op.drop_column("capability_evidence_record", "build_quality")
    op.drop_column("capability_evidence_record", "test_quality")
    op.drop_column("capability_evidence_record", "coverage_limitations")
    op.drop_column("capability_evidence_record", "deep_review_status")
    op.drop_column("capability_evidence_record", "docs_inspected")
    op.drop_column("capability_evidence_record", "build_files_inspected")
    op.drop_column("capability_evidence_record", "test_files_inspected")
    op.drop_column("capability_evidence_record", "source_files_inspected")
    op.drop_column("capability_evidence_record", "files_inspected")
    op.drop_column("capability_evidence_record", "files_discovered")
    op.drop_column("capability_evidence_record", "evidence_source")
    op.drop_column("capability_evidence_record", "commit_sha")
    op.drop_column("capability_evidence_record", "branch")
