"""Suppression ledger.

Every outbound adapter must consult this before sending. No override except an
explicit, audited founder action.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import ChannelType, SuppressionScope
from growthos.domain.models_comms import SuppressionRecord


async def is_suppressed(
    session: AsyncSession,
    *,
    subject_type: str,
    subject_id: str,
    channel: ChannelType,
) -> bool:
    """Return True if any active suppression covers this subject+channel."""
    scopes = [SuppressionScope.ALL_CHANNELS, channel_to_scope(channel)]
    result = await session.execute(
        select(SuppressionRecord).where(
            SuppressionRecord.subject_type == subject_type,
            SuppressionRecord.subject_id == subject_id,
            SuppressionRecord.status == "active",
            SuppressionRecord.scope.in_(scopes),
        )
    )
    records = result.scalars().all()
    for record in records:
        # A record with a specific channel matches only that channel; an
        # all-channels scope matches everything.
        if record.scope is SuppressionScope.ALL_CHANNELS:
            return True
        if record.channel is None or record.channel is channel:
            return True
    return False


def channel_to_scope(channel: ChannelType) -> SuppressionScope:
    mapping = {
        ChannelType.EMAIL: SuppressionScope.EMAIL,
        ChannelType.SMS: SuppressionScope.SMS,
        ChannelType.LINKEDIN: SuppressionScope.LINKEDIN,
        ChannelType.CALL: SuppressionScope.CALL,
    }
    return mapping.get(channel, SuppressionScope.ALL_CHANNELS)
