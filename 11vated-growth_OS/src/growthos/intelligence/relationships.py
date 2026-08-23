"""Pipeline relationship state machine.

A Gmail sender may exist as a Person identity, but a *commercial relationship*
only exists when the founder (or the pipeline) explicitly creates one. This
module records every transition as a RelationshipEvent, keeps the
``pipeline_state`` current, and is the single source of truth the Founder
Inbox gate consults.

States follow the acquisition chain:

    PROSPECT_DISCOVERED -> PROSPECT_QUALIFIED -> OUTREACH_APPROVED
        -> OUTREACH_SENT -> PROSPECT_CONTACTED -> PROSPECT_REPLIED ...

plus explicit founder admissions:

    CLIENT_ACTIVE, PARTNER_ACTIVE, FOLLOW_UP_ACTIVE, PROPOSAL_ACTIVE,
    NEGOTIATION_ACTIVE, RELATIONSHIP_ARCHIVED

``OUTREACH_SENT`` must only be recorded after the communication provider
confirms successful transmission (see ``gmail_send``).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import PipelineState, RelationshipStage
from growthos.domain.models_identity import Relationship, RelationshipEvent
from growthos.shared.ids import new_id

# Valid transitions (from -> {to}). Anything else is rejected.
VALID_TRANSITIONS: dict[PipelineState | None, set[PipelineState]] = {
    None: {
        PipelineState.PROSPECT_DISCOVERED,
        PipelineState.CLIENT_ACTIVE,
        PipelineState.PARTNER_ACTIVE,
        PipelineState.FOLLOW_UP_ACTIVE,
    },
    PipelineState.PROSPECT_DISCOVERED: {
        PipelineState.PROSPECT_QUALIFIED,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.PROSPECT_QUALIFIED: {
        PipelineState.OUTREACH_APPROVED,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.OUTREACH_APPROVED: {
        PipelineState.OUTREACH_SENT,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.OUTREACH_SENT: {
        PipelineState.PROSPECT_CONTACTED,
        PipelineState.PROSPECT_REPLIED,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.PROSPECT_CONTACTED: {
        PipelineState.PROSPECT_REPLIED,
        PipelineState.DISCOVERY_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.PROSPECT_REPLIED: {
        PipelineState.DISCOVERY_ACTIVE,
        PipelineState.PROPOSAL_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.DISCOVERY_ACTIVE: {
        PipelineState.PROPOSAL_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.PROPOSAL_ACTIVE: {
        PipelineState.NEGOTIATION_ACTIVE,
        PipelineState.CLIENT_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.NEGOTIATION_ACTIVE: {
        PipelineState.CLIENT_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.CLIENT_ACTIVE: {
        PipelineState.FOLLOW_UP_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.PARTNER_ACTIVE: {
        PipelineState.FOLLOW_UP_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.FOLLOW_UP_ACTIVE: {
        PipelineState.PROPOSAL_ACTIVE,
        PipelineState.CLIENT_ACTIVE,
        PipelineState.RELATIONSHIP_ARCHIVED,
    },
    PipelineState.RELATIONSHIP_ARCHIVED: set(),
}

FOUNDER_STAGES = {
    RelationshipStage.CLIENT: PipelineState.CLIENT_ACTIVE,
    RelationshipStage.PARTNER: PipelineState.PARTNER_ACTIVE,
    RelationshipStage.ENGAGED: PipelineState.FOLLOW_UP_ACTIVE,
}


async def get_or_create_relationship(
    session: AsyncSession,
    *,
    person_id: str,
) -> Relationship:
    """Return the founder↔person relationship, creating an identity-only row
    if none exists. Creating a row is NOT admission to the pipeline: the
    pipeline_state stays None until a real transition or founder admission."""
    result = await session.execute(
        select(Relationship).where(
            Relationship.subject_type == "founder",
            Relationship.subject_id == "founder",
            Relationship.object_type == "person",
            Relationship.object_id == person_id,
        )
    )
    rel = result.scalar_one_or_none()
    if rel is None:
        rel = Relationship(
            id=new_id(),
            subject_type="founder",
            subject_id="founder",
            object_type="person",
            object_id=person_id,
            stage=RelationshipStage.STRANGER,
            pipeline_state=None,
        )
        session.add(rel)
        await session.flush()
    return rel


async def transition(
    session: AsyncSession,
    *,
    person_id: str,
    to: PipelineState,
    actor: str = "founder",
    description: str | None = None,
    evidence_id: str | None = None,
    channel: str | None = None,
) -> Relationship:
    """Move a person's pipeline state, recording an audited event."""
    rel = await get_or_create_relationship(session, person_id=person_id)
    current = rel.pipeline_state
    allowed = VALID_TRANSITIONS.get(current, set())
    if current == to:
        return rel
    if to not in allowed:
        raise ValueError(
            f"Invalid pipeline transition {current.value if current else None} -> {to.value}"
        )
    rel.pipeline_state = to
    # Keep the coarse relationship stage in sync for consumers.
    if to == PipelineState.CLIENT_ACTIVE:
        rel.stage = RelationshipStage.CLIENT
    elif to == PipelineState.PARTNER_ACTIVE:
        rel.stage = RelationshipStage.PARTNER
    elif to == PipelineState.RELATIONSHIP_ARCHIVED:
        rel.stage = RelationshipStage.DORMANT
    elif rel.stage == RelationshipStage.STRANGER and to not in {
        PipelineState.PROSPECT_DISCOVERED,
        PipelineState.RELATIONSHIP_ARCHIVED,
    }:
        rel.stage = RelationshipStage.ENGAGED
    session.add(
        RelationshipEvent(
            id=new_id(),
            relationship_id=rel.id,
            event_type=f"pipeline:{to.value}",
            description=description or f"Pipeline transition to {to.value}",
            occurred_at=datetime.now(UTC),
            channel=channel,
            evidence_id=evidence_id,
        )
    )
    await session.flush()
    return rel


async def admit_existing_client(
    session: AsyncSession,
    *,
    person_id: str,
    description: str = "Founder admitted existing client",
    evidence_id: str | None = None,
) -> Relationship:
    """Founder-confirmed admission of an existing client (pre-dates GrowthOS)."""
    return await transition(
        session,
        person_id=person_id,
        to=PipelineState.CLIENT_ACTIVE,
        actor="founder",
        description=description,
        evidence_id=evidence_id,
    )


async def mark_outreach_sent(
    session: AsyncSession,
    *,
    person_id: str,
    evidence_id: str | None = None,
) -> Relationship:
    """Record that approved outreach was actually transmitted (post-confirmation)."""
    return await transition(
        session,
        person_id=person_id,
        to=PipelineState.OUTREACH_SENT,
        actor="worker",
        description="Approved outreach successfully sent via communication provider",
        evidence_id=evidence_id,
        channel="email",
    )


async def mark_prospect_replied(
    session: AsyncSession,
    *,
    person_id: str,
    evidence_id: str | None = None,
) -> Relationship:
    return await transition(
        session,
        person_id=person_id,
        to=PipelineState.PROSPECT_REPLIED,
        actor="worker",
        description="Prospect replied to GrowthOS outreach",
        evidence_id=evidence_id,
        channel="email",
    )
