"""Commercial signal intelligence tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-21

Adds ``message_classification`` (structured, versioned classification of each
message) and ``relationship.pipeline_state`` (the pipeline lifecycle that the
Founder Inbox gate consults). Existing rows are not touched — reclassification
runs as a separate, audited command.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_classification",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("message_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("primary_class", sa.String(64), nullable=False),
        sa.Column("secondary_tags", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("relevance_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("attention_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("attention_kinds", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("evidence", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("reasoning", sa.Text(), server_default="", nullable=False),
        sa.Column("classifier_version", sa.String(80), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("message_id", name="uq_message_classification"),
    )
    op.create_index(
        "ix_message_classification_message_id", "message_classification", ["message_id"]
    )
    op.create_index(
        "ix_message_classification_primary_class",
        "message_classification",
        ["primary_class"],
    )
    op.add_column(
        "relationship",
        sa.Column("pipeline_state", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_relationship_pipeline_state", "relationship", ["pipeline_state"]
    )


def downgrade() -> None:
    op.drop_index("ix_relationship_pipeline_state", "relationship")
    op.drop_column("relationship", "pipeline_state")
    op.drop_index("ix_message_classification_primary_class", "message_classification")
    op.drop_index("ix_message_classification_message_id", "message_classification")
    op.drop_table("message_classification")
