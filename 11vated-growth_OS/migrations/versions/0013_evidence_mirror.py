"""Add evidence_mirror table for local read-only repository clones.

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

from growthos.domain.base import jsonb

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Allow capability_id to be NULL for evidence not yet linked to a capability
    op.alter_column("capability_evidence_record", "capability_id", nullable=True)

    op.create_table(
        "evidence_mirror",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("owner", sa.String(200), nullable=False),
        sa.Column("repo_name", sa.String(200), nullable=False),
        sa.Column("full_name", sa.String(400), nullable=False, unique=True),
        sa.Column("remote_url", sa.String(2048), nullable=False),
        sa.Column("local_path", sa.String(2048), nullable=False),
        sa.Column("default_branch", sa.String(200), nullable=True),
        sa.Column("fetched_refs", jsonb, nullable=False, server_default="[]"),
        sa.Column("remote_commit_sha", sa.String(40), nullable=True),
        sa.Column("local_evidence_sha", sa.String(40), nullable=True),
        sa.Column("mirror_state", sa.String(40), server_default="NOT_MIRRORED", nullable=False),
        sa.Column("is_fresh", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorization_source", sa.String(200), server_default="founder_authorized", nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("files_discovered", sa.Integer, server_default="0", nullable=False),
        sa.Column("source_roots", jsonb, nullable=False, server_default="[]"),
        sa.Column("languages", jsonb, nullable=False, server_default="[]"),
        sa.Column("size_kb", sa.Integer, server_default="0", nullable=False),
        sa.Column("last_deep_analysis_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evidence_mirror_owner", "evidence_mirror", ["owner"])
    op.create_index("ix_evidence_mirror_state", "evidence_mirror", ["mirror_state"])


def downgrade() -> None:
    op.alter_column("capability_evidence_record", "capability_id", nullable=False)
    op.drop_index("ix_evidence_mirror_state", table_name="evidence_mirror")
    op.drop_index("ix_evidence_mirror_owner", table_name="evidence_mirror")
    op.drop_table("evidence_mirror")
