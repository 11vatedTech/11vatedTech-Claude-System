"""Gmail message account-scoped uniqueness.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20

Adds ``integration_account_id`` to ``message`` so deduplication is enforced by
the database as (Gmail account + Gmail message id), not only by application
checks. The existing global unique on ``external_message_id`` is kept.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "message",
        sa.Column(
            "integration_account_id",
            sa.dialects.postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_message_integration_account_id",
        "message",
        ["integration_account_id"],
    )
    op.create_foreign_key(
        "fk_message_integration_account",
        "message",
        "integration_account",
        ["integration_account_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_message_account_external",
        "message",
        ["integration_account_id", "external_message_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_message_account_external", "message", type_="unique")
    op.drop_constraint("fk_message_integration_account", "message", type_="foreignkey")
    op.drop_index("ix_message_integration_account_id", "message")
    op.drop_column("message", "integration_account_id")
