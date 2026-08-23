"""Deterministic commercial state machines.

State transition legality is pure, tested software — never delegated to an LLM.
"""

from __future__ import annotations

from growthos.domain.enums import (
    CampaignStatus,
    OutreachState,
    PipelineStage,
)
from growthos.shared.errors import StateTransitionError


def _pipeline_transitions() -> dict[PipelineStage, frozenset[PipelineStage]]:
    return {
        PipelineStage.DISCOVERED: frozenset({PipelineStage.RESEARCHED}),
        PipelineStage.RESEARCHED: frozenset({PipelineStage.QUALIFIED}),
        PipelineStage.QUALIFIED: frozenset(
            {
                PipelineStage.RELATIONSHIP_DEVELOPING,
                PipelineStage.OUTREACH_READY,
            }
        ),
        PipelineStage.RELATIONSHIP_DEVELOPING: frozenset(
            {PipelineStage.OUTREACH_READY, PipelineStage.QUALIFIED}
        ),
        PipelineStage.OUTREACH_READY: frozenset({PipelineStage.CONTACTED}),
        PipelineStage.CONTACTED: frozenset({PipelineStage.ENGAGED}),
        PipelineStage.ENGAGED: frozenset({PipelineStage.DISCOVERY}),
        PipelineStage.DISCOVERY: frozenset({PipelineStage.SOLUTION_DEFINED}),
        PipelineStage.SOLUTION_DEFINED: frozenset({PipelineStage.PROPOSAL_READY}),
        PipelineStage.PROPOSAL_READY: frozenset({PipelineStage.PROPOSAL_SENT}),
        PipelineStage.PROPOSAL_SENT: frozenset({PipelineStage.NEGOTIATION}),
        PipelineStage.NEGOTIATION: frozenset(
            {PipelineStage.WON, PipelineStage.LOST}
        ),
        PipelineStage.WON: frozenset({PipelineStage.HANDOFF}),
        PipelineStage.HANDOFF: frozenset({PipelineStage.DELIVERY}),
        PipelineStage.DELIVERY: frozenset({PipelineStage.COMPLETED}),
        PipelineStage.COMPLETED: frozenset(
            {PipelineStage.EXPANSION, PipelineStage.REFERRAL}
        ),
        PipelineStage.EXPANSION: frozenset({PipelineStage.QUALIFIED}),
        PipelineStage.REFERRAL: frozenset({PipelineStage.QUALIFIED}),
        # Terminal states may only move to DORMANT (except LOST -> nothing).
        PipelineStage.LOST: frozenset({PipelineStage.DORMANT}),
        PipelineStage.DORMANT: frozenset({PipelineStage.QUALIFIED}),
    }


PIPELINE_TRANSITIONS = _pipeline_transitions()

OUTREACH_TRANSITIONS: dict[OutreachState, frozenset[OutreachState]] = {
    OutreachState.DRAFT: frozenset({OutreachState.NEEDS_APPROVAL}),
    OutreachState.NEEDS_APPROVAL: frozenset(
        {OutreachState.APPROVED, OutreachState.STOPPED, OutreachState.DRAFT}
    ),
    OutreachState.APPROVED: frozenset(
        {OutreachState.SCHEDULED, OutreachState.STOPPED, OutreachState.DRAFT}
    ),
    OutreachState.SCHEDULED: frozenset(
        {OutreachState.SENT, OutreachState.STOPPED, OutreachState.DRAFT}
    ),
    OutreachState.SENT: frozenset(
        {OutreachState.REPLIED, OutreachState.STOPPED, OutreachState.OPTED_OUT}
    ),
    OutreachState.REPLIED: frozenset(
        {OutreachState.STOPPED, OutreachState.OPTED_OUT}
    ),
    OutreachState.STOPPED: frozenset({OutreachState.DRAFT}),
    # Terminal.
    OutreachState.OPTED_OUT: frozenset(),
}

CAMPAIGN_TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.DRAFT: frozenset({CampaignStatus.VALIDATING}),
    CampaignStatus.VALIDATING: frozenset(
        {CampaignStatus.ACTIVE, CampaignStatus.STOPPED, CampaignStatus.DRAFT}
    ),
    CampaignStatus.ACTIVE: frozenset(
        {CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.STOPPED}
    ),
    CampaignStatus.PAUSED: frozenset({CampaignStatus.ACTIVE, CampaignStatus.STOPPED}),
    CampaignStatus.COMPLETED: frozenset({CampaignStatus.ACTIVE}),
    CampaignStatus.STOPPED: frozenset({CampaignStatus.DRAFT}),
}


def validate_transition(
    machine: str,
    current: str,
    requested: str,
    transitions: dict,
) -> None:
    """Raise ``StateTransitionError`` unless ``current -> requested`` is legal."""
    try:
        allowed = transitions[current]
    except KeyError:
        raise StateTransitionError(current, requested, machine) from None
    if requested not in allowed and requested != current:
        raise StateTransitionError(current, requested, machine)


def assert_pipeline_transition(
    current: PipelineStage, requested: PipelineStage
) -> None:
    validate_transition(
        "pipeline", current, requested, PIPELINE_TRANSITIONS
    )


def assert_outreach_transition(
    current: OutreachState, requested: OutreachState
) -> None:
    validate_transition(
        "outreach", current, requested, OUTREACH_TRANSITIONS
    )


def assert_campaign_transition(
    current: CampaignStatus, requested: CampaignStatus
) -> None:
    validate_transition(
        "campaign", current, requested, CAMPAIGN_TRANSITIONS
    )
