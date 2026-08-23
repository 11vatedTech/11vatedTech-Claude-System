"""Founder inbox.

Items are generated only from real events and are idempotent per source
(kind + entity_type + entity_id).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import FounderInboxKind, FounderInboxStatus
from growthos.domain.models_comms import FounderInboxItem
from growthos.shared.ids import new_id


async def create_inbox_item(
    session: AsyncSession,
    *,
    kind: FounderInboxKind,
    title: str,
    summary: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    source_evidence_id: str | None = None,
    priority: int = 0,
    due_at: datetime | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[FounderInboxItem, bool]:
    """Create an inbox item, returning (item, created)."""
    existing = await session.execute(
        select(FounderInboxItem).where(
            FounderInboxItem.kind == kind,
            FounderInboxItem.entity_type == entity_type,
            FounderInboxItem.entity_id == entity_id,
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found, False

    item = FounderInboxItem(
        id=new_id(),
        kind=kind,
        title=title,
        summary=summary,
        entity_type=entity_type,
        entity_id=entity_id,
        source_evidence_id=source_evidence_id,
        status=FounderInboxStatus.UNREAD,
        priority=priority,
        due_at=due_at,
        payload=payload or {},
    )
    session.add(item)
    await session.flush()
    return item, True
