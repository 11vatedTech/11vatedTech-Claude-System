"""Autonomy policy gate and suppression ledger (TEST_ONLY)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    ApprovalStatus,
    ChannelType,
    PermissionDecision,
    SuppressionScope,
)
from growthos.domain.models_comms import SuppressionRecord
from growthos.security.approvals import authorize_action, decide_approval
from growthos.security.suppression import is_suppressed
from growthos.shared.errors import PermissionDeniedError


async def test_send_email_requires_approval(session: AsyncSession):
    result = await authorize_action(
        session,
        actor="TEST_ONLY founder",
        action="send_prospect_email",
    )
    assert result.decision is PermissionDecision.REQUIRE_APPROVAL
    assert result.approval_id is not None


async def test_research_is_auto(session: AsyncSession):
    result = await authorize_action(
        session, actor="TEST_ONLY founder", action="research"
    )
    assert result.decision is PermissionDecision.ALLOW


async def test_bypass_robots_txt_is_denied(session: AsyncSession):
    with pytest.raises(PermissionDeniedError):
        await authorize_action(
            session, actor="TEST_ONLY founder", action="bypass_robots_txt"
        )


async def test_suppression_blocks_send(session: AsyncSession):
    session.add(
        SuppressionRecord(
            subject_type="person",
            subject_id="TEST_ONLY-person",
            scope=SuppressionScope.ALL_CHANNELS,
            reason="TEST_ONLY opt out",
            status="active",
        )
    )
    await session.flush()

    assert await is_suppressed(
        session,
        subject_type="person",
        subject_id="TEST_ONLY-person",
        channel=ChannelType.EMAIL,
    )
    assert not await is_suppressed(
        session,
        subject_type="person",
        subject_id="TEST_ONLY-other",
        channel=ChannelType.EMAIL,
    )


async def test_approval_can_be_decided(session: AsyncSession):
    result = await authorize_action(
        session, actor="TEST_ONLY founder", action="send_proposal"
    )
    approval = await decide_approval(
        session,
        approval_id=result.approval_id,
        decision=ApprovalStatus.APPROVED,
        decided_by="TEST_ONLY founder",
    )
    assert approval.status is ApprovalStatus.APPROVED
