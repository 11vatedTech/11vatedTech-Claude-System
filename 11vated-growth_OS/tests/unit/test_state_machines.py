"""State-machine transition legality."""

import pytest

from growthos.domain.enums import CampaignStatus, OutreachState, PipelineStage
from growthos.domain.state_machines import (
    assert_campaign_transition,
    assert_outreach_transition,
    assert_pipeline_transition,
)
from growthos.shared.errors import StateTransitionError


def test_pipeline_forward_path():
    path = [
        PipelineStage.DISCOVERED,
        PipelineStage.RESEARCHED,
        PipelineStage.QUALIFIED,
        PipelineStage.OUTREACH_READY,
        PipelineStage.CONTACTED,
        PipelineStage.ENGAGED,
        PipelineStage.DISCOVERY,
        PipelineStage.SOLUTION_DEFINED,
        PipelineStage.PROPOSAL_READY,
        PipelineStage.PROPOSAL_SENT,
        PipelineStage.NEGOTIATION,
        PipelineStage.WON,
        PipelineStage.HANDOFF,
        PipelineStage.DELIVERY,
        PipelineStage.COMPLETED,
    ]
    for current, nxt in zip(path, path[1:], strict=False):
        assert_pipeline_transition(current, nxt)


def test_pipeline_illegal_skip():
    with pytest.raises(StateTransitionError):
        assert_pipeline_transition(PipelineStage.DISCOVERED, PipelineStage.WON)


def test_pipeline_negotiation_can_lose():
    assert_pipeline_transition(PipelineStage.NEGOTIATION, PipelineStage.LOST)


def test_outreach_needs_approval_before_send():
    assert_outreach_transition(OutreachState.DRAFT, OutreachState.NEEDS_APPROVAL)
    with pytest.raises(StateTransitionError):
        assert_outreach_transition(OutreachState.DRAFT, OutreachState.SENT)


def test_outreach_opted_out_terminal():
    with pytest.raises(StateTransitionError):
        assert_outreach_transition(OutreachState.OPTED_OUT, OutreachState.SENT)


def test_campaign_draft_to_validating():
    assert_campaign_transition(CampaignStatus.DRAFT, CampaignStatus.VALIDATING)
    with pytest.raises(StateTransitionError):
        assert_campaign_transition(CampaignStatus.DRAFT, CampaignStatus.COMPLETED)


def test_noop_transition_allowed():
    assert_pipeline_transition(PipelineStage.QUALIFIED, PipelineStage.QUALIFIED)
