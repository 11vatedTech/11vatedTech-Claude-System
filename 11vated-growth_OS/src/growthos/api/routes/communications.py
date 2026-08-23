"""Communications routes — real conversations and messages only."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.models_comms import Conversation, Message

router = APIRouter(prefix="/communications", tags=["communications"])


@router.get("")
async def list_conversations(session: SessionDep, founder: FounderDep):
    result = await session.execute(
        select(Conversation).order_by(Conversation.last_message_at.desc()).limit(100)
    )
    conversations = result.scalars().all()
    out = []
    for conversation in conversations:
        messages = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.timestamp.asc())
        )
        out.append(
            {
                "id": conversation.id,
                "channel": conversation.channel.value,
                "title": conversation.title,
                "external_thread_id": conversation.external_thread_id,
                "last_message_at": conversation.last_message_at,
                "status": conversation.status,
                "messages": [
                    {
                        "id": m.id,
                        "direction": m.direction,
                        "sender_ref": m.sender_ref,
                        "subject": m.subject,
                        "body": m.body,
                        "timestamp": m.timestamp,
                        "attachments": m.attachments,
                    }
                    for m in messages.scalars().all()
                ],
            }
        )
    return {"conversations": out}
