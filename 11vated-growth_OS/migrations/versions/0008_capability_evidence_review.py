"""Capability evidence metadata and review fields.

Revision ID: 0008
Revises: 0007
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trusted_repository_root", sa.Column("last_scan_at", sa.DateTime(timezone=True)))
    op.add_column("trusted_repository_root", sa.Column("last_error", sa.Text()))
    op.add_column("project_evidence_record", sa.Column("intelligence_profile", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("category", sa.String(80), server_default="DOCUMENTED_CLAIM", nullable=False))
    op.add_column("capability_evidence_record", sa.Column("sensitivity", sa.String(40), server_default="INTERNAL", nullable=False))
    op.create_table(
        "capability_review_event",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_state", sa.String(60)), sa.Column("new_state", sa.String(60), nullable=False),
        sa.Column("changed_fields", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("action", sa.String(80), nullable=False), sa.Column("reason", sa.Text()),
        sa.Column("evidence_context", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("actor", sa.String(120), server_default="founder", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("capability_review_event")
    op.drop_column("capability_evidence_record", "sensitivity")
    op.drop_column("capability_evidence_record", "category")
    op.drop_column("project_evidence_record", "intelligence_profile")
    op.drop_column("trusted_repository_root", "last_error")
    op.drop_column("trusted_repository_root", "last_scan_at")
