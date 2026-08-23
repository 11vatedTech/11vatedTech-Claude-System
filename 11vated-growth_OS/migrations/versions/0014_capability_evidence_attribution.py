"""Add capability_evidence_attribution table.

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "capability_evidence_attribution",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("capability_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repository", sa.String(400), nullable=False),
        sa.Column("file_path", sa.String(2048), nullable=False),
        sa.Column("subsystem", sa.String(200), nullable=True),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("attribution_directness", sa.String(40), nullable=False),
        sa.Column("attribution_reason", sa.Text, nullable=False),
        sa.Column("symbol_name", sa.String(300), nullable=True),
        sa.Column("language", sa.String(80), nullable=True),
        sa.Column("line_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("branch", sa.String(200), nullable=True),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("evidence_source", sa.String(40), server_default="local_mirror", nullable=False),
        sa.Column("attribution_confidence", sa.Float, server_default="0", nullable=False),
        sa.Column("has_validating_test", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("validating_test_path", sa.String(2048), nullable=True),
        sa.Column("validates_subsystem", sa.String(200), nullable=True),
    )
    op.create_index("ix_cap_attr_capability", "capability_evidence_attribution", ["capability_id"])
    op.create_index("ix_cap_attr_repository", "capability_evidence_attribution", ["repository"])
    op.create_index("ix_cap_attr_subsystem", "capability_evidence_attribution", ["subsystem"])
    op.create_unique_constraint(
        "uq_capability_attribution_file", "capability_evidence_attribution",
        ["capability_id", "repository", "file_path"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_capability_attribution_file", "capability_evidence_attribution", type_="unique")
    op.drop_index("ix_cap_attr_subsystem", table_name="capability_evidence_attribution")
    op.drop_index("ix_cap_attr_repository", table_name="capability_evidence_attribution")
    op.drop_index("ix_cap_attr_capability", table_name="capability_evidence_attribution")
    op.drop_table("capability_evidence_attribution")
