"""Initial commercial-graph schema.

Revision ID: 0001
Revises:
Create Date: 2026-08-20

This migration creates the full GrowthOS schema from the declarative metadata.
It is the first revision, so there is no down-revision to preserve.
"""

from __future__ import annotations

from alembic import op

import growthos.domain.models  # noqa: F401  (registers all tables)
from growthos.domain.base import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
