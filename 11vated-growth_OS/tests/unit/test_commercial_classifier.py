"""Unit tests for the commercial relevance classifier.

Covers bulk/automated detection, promotional/newsletter suppression, business
correspondence detection, founder-attention scoring, opportunity-hypothesis
gating, and company-domain inference guards. No network, no DB.
"""

from __future__ import annotations

import asyncio

import pytest

from growthos.domain.enums import MessageClassification
from growthos.intelligence.commercial import (
    classify_message,
    is_automated_message,
    is_bulk_message,
)

CLIENT_CTX = {"is_client": True, "pipeline_state": "CLIENT_ACTIVE"}
PROSPECT_CTX = {"is_contacted_prospect": True, "pipeline_state": "PROSPECT_REPLIED"}


def _msg(**overrides) -> dict:
    base = {
        "sender_email": "jane@acmecorp.com",
        "sender_name": "Jane Doe",
        "subject": "Proposal for your review",
        "body": "Hi Kahlil, attached is the proposal and pricing for the project.",
        "headers": {},
        "labels": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Bulk / automated detection (metadata, not LLM)
# ---------------------------------------------------------------------------


def test_bulk_via_list_unsubscribe_header() -> None:
    headers = {"list-unsubscribe": "<https://unsub.example.com>"}
    assert is_bulk_message(headers, sender_email="a@b.com")
    assert not is_automated_message(headers, sender_email="a@b.com")


def test_bulk_via_precedence() -> None:
    assert is_bulk_message({"precedence": "bulk"}, sender_email="a@b.com")


def test_bulk_via_automated_sender_form() -> None:
    assert is_bulk_message({}, sender_email="no-reply@example.com")
    assert is_bulk_message({}, sender_email="notifications@example.com")
    assert is_bulk_message({}, sender_email="newsletter@example.com")


def test_automated_via_auto_submitted() -> None:
    assert is_automated_message({"auto-submitted": "auto-generated"}, sender_email="a@b.com")
    assert not is_bulk_message({"auto-submitted": "auto-generated"}, sender_email="a@b.com")


# ---------------------------------------------------------------------------
# Promotional / newsletter suppression
# ---------------------------------------------------------------------------


def test_whopper_wednesday_is_promotional_not_task() -> None:
    result = classify_message(
        _msg(
            sender_email="promos-coming@your-way.bk.com",
            subject="🤟 It's Whopper Wednesday! You in?",
            body="Get a Whopper for $3.99 today only. Limited time offer!",
            labels=["CATEGORY_PROMOTIONS"],
        )
    )
    assert result.primary == MessageClassification.PROMOTIONAL
    assert result.attention_score < 40.0


def test_target_promo_is_promotional() -> None:
    result = classify_message(
        _msg(
            sender_email="targetnews@em.target.com",
            subject="Boo-worthy Threshold finds 👻",
            body="Save 25% on new markdowns. Free shipping for members on orders $50+.",
            labels=["CATEGORY_PROMOTIONS"],
        )
    )
    assert result.primary == MessageClassification.PROMOTIONAL
    assert result.attention_score < 40.0


def test_newsletter_with_business_topic_is_still_newsletter() -> None:
    """Bulk metadata dominates generic business language in the body."""
    result = classify_message(
        _msg(
            sender_email="hi@morningdownload.com",
            subject="Home Depot reports",
            body="Market pricing and rate analysis for investors this morning.",
            headers={"list-unsubscribe": "<https://unsub>"},
        )
    )
    assert result.primary == MessageClassification.NEWSLETTER
    assert result.relevance_score < 50.0


def test_gemini_market_newsletter_not_partner() -> None:
    result = classify_message(
        _msg(
            sender_email="hello@news.gemini.com",
            subject="Gemini Markets - Crypto Roars Back",
            body="Bitcoin surpassed $72,000 after the bond buyback announcement. Market pricing trends.",
            headers={"list-id": "gemini-markets"},
        )
    )
    assert result.primary == MessageClassification.NEWSLETTER
    assert result.primary != MessageClassification.BUSINESS_PARTNER


def test_social_notification() -> None:
    result = classify_message(
        _msg(
            sender_email="messages@facebookmail.com",
            subject="Cecelia Mumford sent you a message",
            body="You have a new message on Facebook.",
        )
    )
    assert result.primary == MessageClassification.SOCIAL_NOTIFICATION
    assert result.attention_score < 40.0


def test_transactional_receipt() -> None:
    result = classify_message(
        _msg(
            sender_email="no-reply@store.com",
            subject="Your receipt from Acme Store",
            body="Here is your receipt for order #48291. Payment received.",
            headers={"auto-submitted": "auto-generated"},
        )
    )
    assert result.primary == MessageClassification.TRANSACTIONAL
    assert result.attention_score < 40.0


def test_google_security_alert_overrides_bulk() -> None:
    result = classify_message(
        _msg(
            sender_email="no-reply@accounts.google.com",
            subject="Security alert",
            body="If you didn't allow Base44 access to your Google Account data, someone else may have.",
            headers={"auto-submitted": "auto-generated"},
        )
    )
    assert result.primary == MessageClassification.AUTOMATED_NOTIFICATION
    assert result.attention_score >= 40.0


# ---------------------------------------------------------------------------
# Business correspondence detection
# ---------------------------------------------------------------------------


def test_client_email_is_business_client() -> None:
    result = classify_message(_msg(), relationship_context=CLIENT_CTX)
    assert result.primary == MessageClassification.BUSINESS_CLIENT
    assert result.relevance_score >= 60.0


def test_prospect_reply_is_business_prospect() -> None:
    result = classify_message(
        _msg(
            subject="Re: your proposal",
            body="Thanks! Can you send a revised version by Friday? We are evaluating options.",
        ),
        relationship_context=PROSPECT_CTX,
    )
    assert result.primary == MessageClassification.BUSINESS_PROSPECT
    assert result.attention_score >= 40.0


def test_partner_language_is_business_partner() -> None:
    result = classify_message(
        _msg(
            sender_email="alex@agency.com",
            subject="White-label partnership",
            body="We'd like to discuss a white-label partnership and referral program.",
        )
    )
    assert result.primary == MessageClassification.BUSINESS_PARTNER


def test_no_relationship_no_business_class() -> None:
    """An arbitrary sender is never classified business without pipeline context."""
    result = classify_message(
        _msg(
            sender_email="shein@email.us.shein.com",
            subject="Start from $3.99",
            body="This week's best-selling outfits. Limited time offer!",
            labels=["CATEGORY_PROMOTIONS"],
        )
    )
    assert result.primary != MessageClassification.BUSINESS_NETWORK
    assert result.primary == MessageClassification.PROMOTIONAL


def test_unknown_sender_with_question_is_not_task() -> None:
    """A question mark alone must not create founder attention."""
    result = classify_message(
        _msg(
            sender_email="offers@topcashback.com",
            subject="🔥Activate your $2.50 BONUS!🔥",
            body="Claim your bonus today — you in?",
            labels=["CATEGORY_PROMOTIONS"],
        )
    )
    assert result.primary == MessageClassification.PROMOTIONAL
    assert result.attention_score < 40.0
    assert "explicit_question" not in result.attention_kinds


def test_education_scholarship() -> None:
    result = classify_message(
        _msg(
            sender_email="webmaster@fastweb.com",
            subject="You've Been Matched! New Scholarships Based on Your Profile",
            body="New scholarship opportunities with approaching deadlines. Financial aid for college.",
        )
    )
    assert result.primary == MessageClassification.EDUCATION


def test_education_word_in_newsletter_body_does_not_override_bulk() -> None:
    result = classify_message(
        _msg(
            sender_email="news@thehustle.co",
            subject="The boss is a bot",
            body="Today's business briefing. Of course, we cover startups and trends.",
            headers={"list-id": "hustle"},
        )
    )
    assert result.primary != MessageClassification.EDUCATION


# ---------------------------------------------------------------------------
# Company-domain inference guard
# ---------------------------------------------------------------------------


def test_consumer_domain_never_becomes_company_signal() -> None:
    result = classify_message(
        _msg(
            sender_email="hunnysproductions@gmail.com",
            subject="Pokemon Character Development",
            body="Thoughts on character design for the project.",
        )
    )
    # No bulk, no business terms, no pipeline: stays personal/unknown.
    assert result.primary in {
        MessageClassification.PERSONAL,
        MessageClassification.UNKNOWN,
    }


# ---------------------------------------------------------------------------
# Attention scoring: distinct from relevance
# ---------------------------------------------------------------------------


def test_attention_and_relevance_are_separate() -> None:
    promo = classify_message(
        _msg(
            sender_email="offers@topcashback.com",
            subject="Get up to 101% Cash Back!",
            body="Claim now, limited time.",
            labels=["CATEGORY_PROMOTIONS"],
        )
    )
    client = classify_message(_msg(), relationship_context=CLIENT_CTX)
    # Promo can still carry a low relevance floor, but its attention collapses.
    assert promo.attention_score < client.attention_score
    assert client.relevance_score > promo.relevance_score


def test_classifier_version_is_present() -> None:
    result = classify_message(_msg())
    assert result.version == "commercial-signal-v1"


def test_classifier_is_deterministic() -> None:
    a = classify_message(_msg())
    b = classify_message(_msg())
    assert a.to_dict() == b.to_dict()


# ---------------------------------------------------------------------------
# Async sanity: evaluate_inbox_eligibility refuses arbitrary senders
# ---------------------------------------------------------------------------


def test_pipeline_gate_module_imports() -> None:
    from growthos.intelligence.pipeline_gate import INBOX_ELIGIBLE_PIPELINE_STATES

    assert "CLIENT_ACTIVE" in {s.value for s in INBOX_ELIGIBLE_PIPELINE_STATES}
    assert "PROSPECT_REPLIED" in {s.value for s in INBOX_ELIGIBLE_PIPELINE_STATES}
    assert "PROSPECT_DISCOVERED" not in {s.value for s in INBOX_ELIGIBLE_PIPELINE_STATES}


@pytest.mark.parametrize(
    "state",
    [
        "PROSPECT_DISCOVERED",
        "PROSPECT_QUALIFIED",
        "RELATIONSHIP_ARCHIVED",
    ],
)
def test_non_eligible_pipeline_states_are_excluded(state: str) -> None:
    from growthos.intelligence.pipeline_gate import INBOX_ELIGIBLE_PIPELINE_STATES

    values = {s.value for s in INBOX_ELIGIBLE_PIPELINE_STATES}
    assert state not in values


def test_transition_invalid() -> None:
    from growthos.intelligence.relationships import VALID_TRANSITIONS

    with pytest.raises(ValueError):
        _transition_guard(VALID_TRANSITIONS, "PROSPECT_DISCOVERED", "CLIENT_ACTIVE")


def _transition_guard(table, current, to) -> None:
    from growthos.domain.enums import PipelineState

    allowed = table.get(PipelineState(current), set())
    if PipelineState(to) not in allowed:
        raise ValueError("invalid transition")


def test_async_eligibility_requires_person() -> None:
    """No DB — a sender with no Person record is never eligible."""
    from unittest.mock import AsyncMock, MagicMock

    from growthos.intelligence.pipeline_gate import evaluate_inbox_eligibility

    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    eligible, reason, ctx = asyncio.run(
        evaluate_inbox_eligibility(session, sender_email="stranger@example.com")
    )
    assert eligible is False
    assert "no GrowthOS person record" in reason
    assert ctx == {}
