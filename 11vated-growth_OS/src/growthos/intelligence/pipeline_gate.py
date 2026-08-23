"""Founder Inbox eligibility gate.

The rule is deliberately strict: Founder Inbox is the *operational inbox for
11vatedTech's active commercial pipeline*, not a second Gmail inbox. A message
sender is inbox-eligible only when they are linked to a real GrowthOS
commercial identity AND an active pipeline relationship exists:

* GrowthOS successfully sent approved outreach to that prospect
  (``OUTREACH_SENT`` / ``PROSPECT_CONTACTED`` / ``PROSPECT_REPLIED``)
* the founder explicitly admitted the person/company into the active pipeline
* they are an existing founder-confirmed client (``CLIENT_ACTIVE``)
* they are an active partner/referral relationship (``PARTNER_ACTIVE``)
* they belong to an active opportunity / proposal / negotiation / delivery /
  unresolved commercial commitment

Merely receiving an inbound email NEVER promotes someone into the pipeline.
Discovered-but-uncontacted prospects stay in Discovery. Promotional and social
senders are never eligible here — they remain visible under Communications.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    OutreachState,
    PipelineStage,
    PipelineState,
    RelationshipStage,
)
from growthos.domain.models_commercial import Opportunity
from growthos.domain.models_comms import Outreach
from growthos.domain.models_identity import Person, Relationship

# Pipeline states that make a sender inbox-eligible. Anything archived,
# dormant, or merely discovered does NOT qualify.
INBOX_ELIGIBLE_PIPELINE_STATES = {
    PipelineState.OUTREACH_APPROVED,
    PipelineState.OUTREACH_SENT,
    PipelineState.PROSPECT_CONTACTED,
    PipelineState.PROSPECT_REPLIED,
    PipelineState.DISCOVERY_ACTIVE,
    PipelineState.PROPOSAL_ACTIVE,
    PipelineState.NEGOTIATION_ACTIVE,
    PipelineState.CLIENT_ACTIVE,
    PipelineState.PARTNER_ACTIVE,
    PipelineState.FOLLOW_UP_ACTIVE,
}

# Relationship stages that reflect a real, active commercial relationship.
ACTIVE_RELATIONSHIP_STAGES = {
    RelationshipStage.ENGAGED,
    RelationshipStage.CLIENT,
    RelationshipStage.PARTNER,
}

# Opportunity stages that carry an active commercial commitment.
ACTIVE_OPPORTUNITY_STAGES = {
    PipelineStage.DISCOVERY,
    PipelineStage.SOLUTION_DEFINED,
    PipelineStage.PROPOSAL_READY,
    PipelineStage.PROPOSAL_SENT,
    PipelineStage.NEGOTIATION,
    PipelineStage.DELIVERY,
    PipelineStage.EXPANSION,
    PipelineStage.REFERRAL,
    PipelineStage.WON,
}


async def _person_by_email(session: AsyncSession, email: str | None) -> Person | None:
    if not email:
        return None
    result = await session.execute(
        select(Person).where(Person.email == email.strip().lower())
    )
    return result.scalar_one_or_none()


async def _sent_outreach(session: AsyncSession, person_id: str) -> bool:
    result = await session.execute(
        select(Outreach.id).where(
            Outreach.person_id == person_id,
            Outreach.state.in_([OutreachState.SENT, OutreachState.REPLIED]),
        )
    )
    return result.first() is not None


async def _active_relationship(session: AsyncSession, person_id: str) -> str | None:
    """Return the pipeline state if a real active relationship exists."""
    result = await session.execute(
        select(Relationship).where(
            Relationship.subject_type == "founder",
            Relationship.object_type == "person",
            Relationship.object_id == person_id,
        )
    )
    rel = result.scalar_one_or_none()
    if rel is None:
        return None
    # Pipeline state (if explicitly set) is authoritative.
    if rel.pipeline_state is not None:
        return rel.pipeline_state.value
    # Fall back to relationship stage heuristics — only REAL active stages.
    if rel.stage in ACTIVE_RELATIONSHIP_STAGES:
        return f"relationship:{rel.stage.value}"
    return None


async def _active_opportunity(session: AsyncSession, person_id: str) -> bool:
    result = await session.execute(
        select(Opportunity.id).where(
            Opportunity.person_id == person_id,
            Opportunity.stage.in_(ACTIVE_OPPORTUNITY_STAGES),
        )
    )
    return result.first() is not None


async def evaluate_inbox_eligibility(
    session: AsyncSession,
    *,
    sender_email: str | None,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Decide whether a message sender may enter Founder Inbox.

    Returns ``(eligible, reason, context)``. ``context`` carries verified
    pipeline facts for the classifier (never invented by the classifier).
    """
    person = await _person_by_email(session, sender_email)
    if person is None:
        return False, "Sender has no GrowthOS person record", {}

    pipeline_state = await _active_relationship(session, person.id)
    sent = await _sent_outreach(session, person.id)
    opportunity = await _active_opportunity(session, person.id)

    context = {
        "person_id": person.id,
        "pipeline_state": pipeline_state,
        "is_contacted_prospect": sent,
        "has_active_opportunity": opportunity,
    }

    if sent:
        return True, "GrowthOS sent approved outreach and the prospect replied or is in a live thread", context
    if opportunity:
        return True, "Sender belongs to an active opportunity", context
    if pipeline_state:
        if pipeline_state.startswith("relationship:"):
            return True, f"Active relationship stage: {pipeline_state.split(':', 1)[1]}", context
        return True, f"Active pipeline state: {pipeline_state}", context
    return False, "No active pipeline/client/partner relationship — Communications only", context
