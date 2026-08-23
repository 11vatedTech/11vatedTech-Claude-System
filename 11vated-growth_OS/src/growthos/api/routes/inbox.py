"""Founder inbox routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.enums import FounderInboxStatus
from growthos.domain.models_comms import FounderInboxItem

router = APIRouter(prefix="/inbox", tags=["inbox"])


class InboxActionIn(BaseModel):
    action: str  # read | actioned | dismissed


def _serialize(item: FounderInboxItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "kind": item.kind.value,
        "title": item.title,
        "summary": item.summary,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "status": item.status.value,
        "priority": item.priority,
        "due_at": item.due_at,
        "created_at": item.created_at,
        "payload": item.payload,
    }


@router.get("")
async def list_inbox(session: SessionDep, founder: FounderDep):
    result = await session.execute(
        select(FounderInboxItem)
        .order_by(FounderInboxItem.priority.desc(), FounderInboxItem.created_at.desc())
        .limit(100)
    )
    return {"items": [_serialize(i) for i in result.scalars().all()]}


@router.post("/{item_id}/action")
async def inbox_action(
    session: SessionDep, founder: FounderDep, item_id: str, body: InboxActionIn
):
    result = await session.execute(
        select(FounderInboxItem).where(FounderInboxItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    try:
        item.status = FounderInboxStatus(body.action)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid action") from exc
    return _serialize(item)
