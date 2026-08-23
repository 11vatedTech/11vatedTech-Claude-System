"""GitHub portfolio evidence census: profiles, repository evidence, families.

Revision ID: 0011
Revises: 0010
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def _uuid() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True)


def upgrade() -> None:
    op.create_table(
        "github_profile_evidence_source",
        _uuid(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("login", sa.String(200), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("authorization_state", sa.String(60), server_default="AUTHORIZED_READ_ONLY", nullable=False),
        sa.Column("visibility_state", sa.String(60), server_default="UNSCANNED", nullable=False),
        sa.Column("last_scan_at", sa.DateTime(timezone=True)),
        sa.Column("repositories_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("repositories_analyzed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error", sa.Text()),
        sa.UniqueConstraint("login", name="uq_github_profile_login"),
    )

    op.create_table(
        "project_family",
        _uuid(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("primary_languages", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("evidence_strength", sa.String(60), server_default="EMPTY_OR_MINIMAL", nullable=False),
        sa.Column("evidence_summary", sa.Text(), server_default="", nullable=False),
        sa.Column("overlap_note", sa.Text()),
        sa.Column("capability_candidates", sa.JSON(), server_default="[]", nullable=False),
        sa.UniqueConstraint("slug", name="uq_project_family_slug"),
    )

    op.create_table(
        "repository_evidence",
        _uuid(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("github_profile_evidence_source.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("full_name", sa.String(400), nullable=False),
        sa.Column("html_url", sa.String(2048)),
        sa.Column("description", sa.Text()),
        sa.Column("topics", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("visibility", sa.String(40), server_default="public", nullable=False),
        sa.Column("archived", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("fork", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("default_branch", sa.String(200)),
        sa.Column("primary_language", sa.String(80)),
        sa.Column("languages", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("size_kb", sa.Integer(), server_default="0", nullable=False),
        sa.Column("stargazers", sa.Integer(), server_default="0", nullable=False),
        sa.Column("readme_present", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("source_present", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("tests_present", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("ci_build_present", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("releases_present", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("architecture_docs_present", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("empty_or_minimal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("evidence_strength", sa.String(60), server_default="EMPTY_OR_MINIMAL", nullable=False),
        sa.Column("evidence_value_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("score_breakdown", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("pushed_at", sa.DateTime(timezone=True)),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("project_family.id", ondelete="SET NULL")),
        sa.UniqueConstraint("full_name", name="uq_repository_evidence_full_name"),
    )
    op.create_index("ix_repository_evidence_profile_id", "repository_evidence", ["profile_id"])
    op.create_index("ix_repository_evidence_family_id", "repository_evidence", ["family_id"])


def downgrade() -> None:
    op.drop_index("ix_repository_evidence_family_id", table_name="repository_evidence")
    op.drop_index("ix_repository_evidence_profile_id", table_name="repository_evidence")
    op.drop_table("repository_evidence")
    op.drop_table("project_family")
    op.drop_table("github_profile_evidence_source")
