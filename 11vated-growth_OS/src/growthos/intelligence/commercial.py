"""Commercial signal intelligence.

Deterministic classification of email into commercial-relevance classes, a
Commercial Relevance Score (0-100) and a separate Founder Attention Score
(0-100). Bulk/automated signals come from email metadata (headers, sender
patterns) — never left to the model. Classification is a *layer on top of*
preserved source evidence: a promotional email is still stored, it just stops
driving Founder Inbox items.

The model reasons; the software governs. All rules here are deterministic and
versioned so reclassification is reproducible and auditable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from growthos.domain.enums import FounderAttentionKind, MessageClassification

CLASSIFIER_VERSION = "commercial-signal-v1"

# ---------------------------------------------------------------------------
# Deterministic signals
# ---------------------------------------------------------------------------

CONSUMER_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "yahoo.com",
    "yahoo.co.uk", "aol.com", "icloud.com", "me.com", "mac.com", "live.com",
    "msn.com", "proton.me", "protonmail.com", "gmx.com", "zoho.com",
}

# Local-part prefixes that strongly indicate automated/bulk senders.
AUTOMATED_LOCAL_PARTS = re.compile(
    r"^(no-?reply|donotreply|do-not-reply|notifications?|newsletters?|"
    r"updates?|alerts?|info|marketing|promo(tions)?|offers?|deals?|"
    r"mailer|dispatch|postmaster|bounces?|team|hello|support|service|"
    r"account|security|billing|admin|contact|automated)\b",
    re.IGNORECASE,
)

PROMOTIONAL_SUBJECT = re.compile(
    r"(% off|save \d+%|sale|deal|reward|bonus|cash ?back|free (shipping|gift|trial)|"
    r"coupon|discount|last chance|act now|don'?t miss|limited time|exclusive offer|"
    r"claim your|win |winner|earn \d+|get \d+%|up to \d+%|\$\d+|today only|"
    r"hurry|in stock|new arrival|restock|flash sale|promo code|referral code)",
    re.IGNORECASE,
)

URGENCY_SUBJECT = re.compile(
    r"(!+|urgent|immediately|asap|right now|today|tonight|final|end(ing)? "
    r"(today|soon|tonight)|expires?|deadline|countdown)",
    re.IGNORECASE,
)

BUSINESS_TERMS = re.compile(
    r"\b(business|client|prospect|partner|contract|proposal|agreement|invoice|"
    r"payment|pricing|quote|budget|project|deliverable|milestone|statement of work|"
    r"white-?label|referral|commission|retainer|subscription|licens|enterprise|"
    r"integration|API|requirements|estimate|rate|scope|vendor|procurement|"
    r"NDA|MOU|purchase order|onboarding|implementation|support plan|SLA)\b",
    re.IGNORECASE,
)

PARTNERSHIP_TERMS = re.compile(
    r"\b(partner|collaborat|white-?label|co-brand|joint venture|affiliate|"
    r"resell|distribut|referral program|strategic alliance|integration "
    r"partnership|marketplace)\b",
    re.IGNORECASE,
)

MEETING_TERMS = re.compile(
    r"\b(call|meeting|demo|intro(duction)?|schedule|calendar|availability|"
    r"book a|let'?s (talk|chat|connect)|zoom|google meet|discovery call)\b",
    re.IGNORECASE,
)

PROPOSAL_TERMS = re.compile(
    r"\b(proposal|quote|estimate|statement of work|pricing|budget|cost|"
    r"rate card|scoping|requirements?|RFP|RFQ)\b",
    re.IGNORECASE,
)

PAYMENT_TERMS = re.compile(
    r"\b(payment|invoice|overdue|past due|refund|charge|credit card|wire|"
    r"ACH|deposit|balance due|billing issue|payment failed|receipt)\b",
    re.IGNORECASE,
)

# Strong transactional language: an *order/receipt/payment lifecycle* event.
# Used to lift a bulk message out of NEWSLETTER only when the signal is
# unambiguous (a receipt, an invoice, a payment notice) — not generic
# business discussion about pricing or wires in a market newsletter.
STRONG_TRANSACTIONAL_TERMS = re.compile(
    r"\b(invoice (attached|available|due)|order (confirmation|received|shipped|"
    r"status|details)|payment (received|processed|failed|declined)|"
    r"receipt (for|attached|from)|your (receipt|order|invoice)|"
    r"billing (statement|notice)|payment due|autopay|subscription (renewed|"
    r"payment|billing)|tax (receipt|document)|transaction (confirmation|"
    r"receipt))\b",
    re.IGNORECASE,
)

SECURITY_TERMS = re.compile(
    r"\b(security alert|unusual activity|sign-?in attempt|new device|"
    r"verify your|verification code|password reset|2FA|two-?factor|"
    r"compromised|breach|phishing|suspicious)\b",
    re.IGNORECASE,
)

# Account-directed security language: a direct alert TO the founder about
# THEIR account, not a news article discussing security topics.
STRONG_SECURITY_TERMS = re.compile(
    r"\b(we (detected|blocked|stopped) (an? )?(unusual|suspicious|new) "
    r"(activity|sign-?in|login)|your account (was|has been)|sign-?in "
    r"attempt (on|to) your account|someone (tried|attempted) to sign in|"
    r"new device (signed|logged) in|we are verifying it is you|confirm it "
    r"is you|security (code|alert) for your account|password reset (request|"
    r"link) for your account|reset your password|unusual activity (on|in) "
    r"your account|your account was (locked|temporarily suspended))\b",
    re.IGNORECASE,
)

SYSTEM_FAILURE_TERMS = re.compile(
    r"\b(service (outage|disruption)|system (outage|down|degraded)|"
    r"build failed|deployment failed|pipeline failed|incident (alert|report)|"
    r"sev(erity)? [123] incident|infrastructure (alert|incident)|"
    r"production (outage|down|incident))\b",
    re.IGNORECASE,
)

DELIVERABLE_TERMS = re.compile(
    r"\b(deliver|send (me|us)|need (the|this|it)|please provide|can you "
    r"(share|send|provide|prepare)|attach|revised|updated version|final "
    r"(version|draft)|screenshot|spec|documentation|files?)\b",
    re.IGNORECASE,
)

QUESTION_TERMS = re.compile(
    r"\b(please advise|what (is|are|about)|when (can|will|should)|how (can|do|"
    r"should)|would you|can you|could you|are you|is it possible|any update|"
    r"thoughts\?|let me know|keep me posted|following up on)\b",
    re.IGNORECASE,
)

DEADLINE_TERMS = re.compile(
    r"\b(by (monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|"
    r"eod|end of (the )?day|next week|friday|this week|\d{1,2}[/-]\d{1,2}"
    r"(?:[/-]\d{2,4})?)|deadline|due (date|by)|needed by|required by|"
    r"before (monday|tuesday|wednesday|thursday|friday|end of))\b",
    re.IGNORECASE,
)

COMMITMENT_TERMS = re.compile(
    r"\b(i|we) (will|'ll|promise|commit to|get back to you|send (you|it)|"
    r"follow up)|as promised|per our (conversation|agreement|discussion)\b",
    re.IGNORECASE,
)

OBJECTION_TERMS = re.compile(
    r"\b(too expensive|not (interested|a priority|ready)|no budget|can'?t "
    r"afford|too busy|happy with (current|existing)|not the right time|"
    r"we'?re (good|fine) with)\b",
    re.IGNORECASE,
)

BUYING_TERMS = re.compile(
    r"\b(interested in|looking for|need help with|considering|exploring|"
    r"evaluating|we need|we'?re looking|want to (buy|purchase|use|try)|"
    r"would like to (work|discuss|talk))\b",
    re.IGNORECASE,
)

EDUCATION_TERMS = re.compile(
    r"\b(scholarship (deadline|opportunity|match)|financial aid|FAFSA|tuition|"
    r"student loan|college (application|admission)|university admission|"
    r"course enrollment|class registration|academic (year|calendar)|"
    r"degree program|admissions office|financial aid office)\b",
    re.IGNORECASE,
)

# Known consumer/social platforms that are not commercial relationships.
SOCIAL_DOMAINS = {
    "facebookmail.com", "linkedin.com", "e.linkedin.com", "connect.linkedin.com",
    "messaging.linkedin.com", "notifications.linkedin.com", "twitter.com",
    "x.com", "instagram.com", "mail.instagram.com", "tiktok.com",
    "notification@service.tiktok.com", "mail.tiktok.com", "discord.com",
    "pinterest.com", "snapchat.com", "youtube.com", "mail.youtube.com",
    "redditmail.com", "mail.reddit.com", "skool.com", "circle.so",
}

# Domains that are almost always consumer e-commerce or mass-retail senders.
CONSUMER_RETAIL_DOMAINS = {
    "shein.com", "email.us.shein.com", "temuemail.com", "e.target.com",
    "em.target.com", "e.xbox.com", "e.avis.com", "e.upperdeck.com",
    "updates.finishline.com", "your-way.bk.com", "r.email.draftkings.com",
    "promo.spree.com", "app.hardrockbet.com", "a.pulsz.com", "em.temu.com",
    "e.bestbuy.com", "e.nike.com", "e.adidas.com", "e.walmart.com",
    "microsoftstore.microsoft.com",
}

# Sender domains reliably associated with education (schools, scholarship
# platforms, student-loan providers). These override the generic bulk label.
EDUCATION_DOMAINS = {
    "fastweb.com",
    "scholarshipowl.com",
    "scholarships.com",
    "scholarships360.org",
    "salliemae.com",
    "soslprospect.salliemae.com",
    "fullsail.edu",
    "collegeboard.org",
    "fafsa.gov",
    "studentaid.gov",
    "aclj.org",
}

# Senders reliably used for account-security notifications (Google, GitHub,
# Apple, Microsoft, LinkedIn). These override the generic bulk label.
KNOWN_SECURITY_SENDERS = {
    "accounts.google.com",
    "security.google.com",
    "security-noreply@linkedin.com",
    "noreply@github.com",
    "security@github.com",
    "no-reply@apple.com",
    "security@microsoft.com",
}

# Sender domains that are reliably newsletter/content publishers (metadata).
NEWSLETTER_DOMAINS = {
    "morningdownload.com",
    "tldrnewsletter.com",
    "thehustle.co",
    "substack.com",
    "mail.kalshi.com",
    "news.gemini.com",
    "news.nvidia.com",
    "newsletter.example.com",
}

# Domain prefixes/substrings that are deterministic bulk indicators.
BULK_DOMAIN_PREFIXES = ("e.", "em.", "mail.", "news.", "updates.", "connect.", "email.", "notifications.")
BULK_DOMAIN_SUBSTRINGS = ("newsletter", "marketing", "mailing", "mailers", "campaigns", "sendgrid", "mailchimp")

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class ClassificationResult:
    primary: MessageClassification
    secondary_tags: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    attention_score: float = 0.0
    attention_kinds: list[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    version: str = CLASSIFIER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_class": self.primary.value,
            "secondary_tags": self.secondary_tags,
            "relevance_score": self.relevance_score,
            "attention_score": self.attention_score,
            "attention_kinds": self.attention_kinds,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "classifier_version": self.version,
        }


def _ev(evidence: list[dict[str, Any]], signal: str, detail: str, weight: float = 0.5) -> None:
    evidence.append({"signal": signal, "detail": detail[:300], "weight": weight})


def _sender_local_part(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    return email.split("@")[0].lower()


def _sender_domain(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    return email.split("@")[1].lower()


def is_bulk_message(headers: dict[str, Any], *, sender_email: str | None) -> bool:
    """True when metadata strongly indicates a bulk/mailing-list message."""
    if headers.get("list-unsubscribe") or headers.get("list-id") or headers.get("list-post"):
        return True
    if headers.get("x-mailing-list") or headers.get("x-campaign-id") or headers.get("x-feedback-id"):
        return True
    if (headers.get("precedence") or "").lower() in {"bulk", "junk", "list"}:
        return True
    return AUTOMATED_LOCAL_PARTS.match(_sender_local_part(sender_email)) is not None


def is_automated_message(headers: dict[str, Any], *, sender_email: str | None) -> bool:
    """True when metadata indicates an automated/system message (may still matter)."""
    auto = (headers.get("auto-submitted") or "").lower()
    if auto and auto not in {"no"}:
        return True
    if headers.get("x-auto-response-suppress"):
        return True
    return AUTOMATED_LOCAL_PARTS.match(_sender_local_part(sender_email)) is not None


def _normalize(text: str | None) -> str:
    return (text or "").lower()


def classify_message(
    parsed: dict[str, Any],
    *,
    relationship_context: dict[str, Any] | None = None,
) -> ClassificationResult:
    """Classify one parsed message.

    ``relationship_context`` may carry pipeline facts about the sender, e.g.
    ``{"pipeline_state": "...", "is_client": True, "is_partner": True}`` —
    but the classifier never invents a relationship; it only *uses* one that
    the caller verified from persisted state.
    """
    evidence: list[dict[str, Any]] = []
    headers = parsed.get("headers") or {}
    labels = [str(label).lower() for label in (parsed.get("labels") or [])]
    sender_email = parsed.get("sender_email")
    sender_name = parsed.get("sender_name")
    subject = _normalize(parsed.get("subject"))
    body = _normalize(parsed.get("body"))
    text = f"{subject}\n{body}"
    domain = _sender_domain(sender_email)
    local = _sender_local_part(sender_email)

    # Gmail category labels are themselves deterministic bulk/automated signals.
    label_bulk = any(
        "promotions" in label or "forums" in label or "updates" in label
        for label in labels
    )
    label_social = any("social" in label for label in labels)
    if label_bulk:
        _ev(evidence, "gmail_label", "Gmail category label indicates bulk content (PROMOTIONS/UPDATES/FORUMS)")
    if label_social:
        _ev(evidence, "gmail_label_social", "Gmail SOCIAL category label")

    # Domain-level bulk indicators (newsletter publishers, bulk prefixes).
    domain_bulk = domain in NEWSLETTER_DOMAINS or any(
        domain.startswith(prefix) for prefix in BULK_DOMAIN_PREFIXES
    ) or any(sub in domain for sub in BULK_DOMAIN_SUBSTRINGS)
    if domain_bulk:
        _ev(evidence, "domain_bulk", f"Sender domain {domain!r} is a known newsletter/bulk domain")

    bulk = is_bulk_message(headers, sender_email=sender_email) or label_bulk or domain_bulk
    automated = is_automated_message(headers, sender_email=sender_email)

    tags: list[str] = []
    if bulk:
        tags.append("bulk")
        _ev(evidence, "bulk_headers", "List-Unsubscribe/List-ID/Precedence bulk or automated sender form")
    if automated:
        tags.append("automated")
        _ev(evidence, "automated_headers", "Auto-Submitted / X-Auto-Response-Suppress or automated sender form")

    promo_subject = bool(PROMOTIONAL_SUBJECT.search(subject))
    business = bool(BUSINESS_TERMS.search(text))
    partnership = bool(PARTNERSHIP_TERMS.search(text))
    meeting = bool(MEETING_TERMS.search(text))
    proposal = bool(PROPOSAL_TERMS.search(text))
    payment = bool(PAYMENT_TERMS.search(text))
    strong_transactional = bool(STRONG_TRANSACTIONAL_TERMS.search(text))
    if strong_transactional:
        _ev(evidence, "strong_transactional", "Unambiguous order/receipt/payment-lifecycle language")
    security = bool(SECURITY_TERMS.search(text))
    known_security_sender = (
        domain in KNOWN_SECURITY_SENDERS or sender_email in KNOWN_SECURITY_SENDERS
    )
    if known_security_sender:
        _ev(evidence, "known_security_sender", f"Known account-security sender {sender_email!r}")
    strong_security = bool(STRONG_SECURITY_TERMS.search(text)) or (
        known_security_sender and security
    )
    if strong_security:
        _ev(evidence, "strong_security", "Account-directed security alert language")
    system_failure = bool(SYSTEM_FAILURE_TERMS.search(text))
    education_domain = domain in EDUCATION_DOMAINS or domain.endswith(".edu")
    education = education_domain or bool(EDUCATION_TERMS.search(text))
    social = (
        label_social
        or domain in SOCIAL_DOMAINS
        or any(d in domain for d in ("facebookmail", "linkedin"))
    )
    retail = domain in CONSUMER_RETAIL_DOMAINS or any(d in domain for d in ("shein", "temu", "target"))

    # Known relationship context (verified by the caller from persisted state).
    ctx = relationship_context or {}
    is_client = bool(ctx.get("is_client"))
    is_partner = bool(ctx.get("is_partner"))
    is_contacted_prospect = bool(ctx.get("is_contacted_prospect"))
    pipeline_state = ctx.get("pipeline_state")

    # --- Primary classification decision tree -------------------------------
    # Priority: bulk/automated metadata dominates generic business language.
    # A mailing list that *talks about* business is still a newsletter. Only
    # verified pipeline relationships or security/system/payment overrides can
    # lift a message out of the bulk bucket. This is what prevents "Whopper
    # Wednesday — you in?" and "Crypto markets rally" from becoming tasks.
    primary: MessageClassification = MessageClassification.UNKNOWN
    reasoning = ""

    if education_domain:
        primary = MessageClassification.EDUCATION
        tags.append("education")
        reasoning = "Sender domain is an educational institution or scholarship platform"
    elif education and not bulk:
        primary = MessageClassification.EDUCATION
        tags.append("education")
        reasoning = "Education terminology detected from a non-bulk sender"
    elif social and not (business and (is_client or is_partner)):
        primary = MessageClassification.SOCIAL_NOTIFICATION
        tags.append("social")
        reasoning = "Sender domain is a known social platform"
    elif bulk and (promo_subject or retail):
        primary = MessageClassification.PROMOTIONAL
        tags.append("promotional")
        reasoning = "Bulk/mailing-list sender with promotional signals"
    elif bulk and (strong_security or system_failure):
        primary = MessageClassification.AUTOMATED_NOTIFICATION
        tags.append("automated")
        reasoning = "Bulk sender but account-directed security/system language is a real override"
    elif bulk and strong_transactional:
        primary = MessageClassification.TRANSACTIONAL
        tags.append("transactional")
        reasoning = "Bulk sender with unambiguous receipt/order/payment lifecycle language"
    elif bulk:
        primary = MessageClassification.NEWSLETTER
        tags.append("newsletter")
        reasoning = "Bulk/mailing-list message (newsletter)"
    elif automated and security:
        primary = MessageClassification.AUTOMATED_NOTIFICATION
        tags.append("security")
        reasoning = "Automated message with security terminology"
    elif automated and system_failure:
        primary = MessageClassification.AUTOMATED_NOTIFICATION
        tags.append("system")
        reasoning = "Automated message with system-failure terminology"
    elif automated and (payment or "receipt" in text or "order" in subject):
        primary = MessageClassification.TRANSACTIONAL
        tags.append("transactional")
        reasoning = "Automated message with payment/order language"
    elif automated:
        primary = MessageClassification.AUTOMATED_NOTIFICATION
        reasoning = "Automated message without a security/system/payment override"
    elif promo_subject and not business:
        primary = MessageClassification.PROMOTIONAL
        tags.append("promotional")
        reasoning = "Promotional subject language without business terminology"
    elif is_client or pipeline_state in {"CLIENT_ACTIVE", "PROPOSAL_ACTIVE", "NEGOTIATION_ACTIVE"}:
        primary = MessageClassification.BUSINESS_CLIENT
        tags.append("client")
        reasoning = "Sender has an active client relationship in the pipeline"
    elif is_partner or pipeline_state in {"PARTNER_ACTIVE", "FOLLOW_UP_ACTIVE"}:
        primary = MessageClassification.BUSINESS_PARTNER
        tags.append("partner")
        reasoning = "Sender has an active partner relationship in the pipeline"
    elif is_contacted_prospect or pipeline_state in {
        "PROSPECT_CONTACTED", "PROSPECT_REPLIED", "OUTREACH_SENT", "DISCOVERY_ACTIVE",
    }:
        primary = MessageClassification.BUSINESS_PROSPECT
        tags.append("prospect")
        reasoning = "Sender is a contacted prospect in the pipeline"
    elif partnership:
        primary = MessageClassification.BUSINESS_PARTNER
        tags.append("partnership")
        reasoning = "Partnership/collaboration language from a non-bulk sender"
    elif business and meeting:
        primary = MessageClassification.BUSINESS_NETWORK
        tags.append("network")
        reasoning = "Business terminology with meeting/connection language"
    elif business and proposal:
        primary = MessageClassification.BUSINESS_SERVICE
        tags.append("service")
        reasoning = "Business terminology with proposal/quote language"
    elif business and payment:
        primary = MessageClassification.BUSINESS_VENDOR
        tags.append("vendor")
        reasoning = "Business terminology with payment/invoice language"
    elif business and not bulk and domain not in CONSUMER_EMAIL_DOMAINS:
        primary = MessageClassification.BUSINESS_NETWORK
        tags.append("network")
        reasoning = "Business terminology from a non-bulk, non-promotional sender"
    elif domain in CONSUMER_EMAIL_DOMAINS or local in {"kahlil", "founder"} or sender_name:
        # A personally addressed message from a human sender on a consumer
        # provider. Generic business words ("project", "rate") in personal
        # mail are NOT a commercial relationship signal.
        primary = MessageClassification.PERSONAL
        tags.append("personal")
        reasoning = "Personal-domain sender without strong business signals"
    elif bulk:
        primary = MessageClassification.NEWSLETTER
        tags.append("newsletter")
        reasoning = "Bulk mailing-list message"
    elif local in {"kahlil", "founder"} or sender_name:
        # A personally addressed message from a named human sender.
        if "job" in text or "interview" in text or "hiring" in text:
            primary = MessageClassification.BUSINESS_ADMIN
            tags.append("admin")
            reasoning = "Named sender, recruitment/HR language"
        else:
            primary = MessageClassification.PERSONAL
            tags.append("personal")
            reasoning = "Named human sender without bulk or business signals"
    else:
        primary = MessageClassification.UNKNOWN
        reasoning = "No strong commercial, bulk, or personal signal"

    # --- Commercial Relevance Score (0-100) ---------------------------------
    score = 20.0  # baseline: mail that exists
    if bulk:
        score -= 25.0
    if promo_subject:
        score -= 20.0
    if retail or social:
        score -= 15.0
    if primary in {
        MessageClassification.BUSINESS_CLIENT,
        MessageClassification.BUSINESS_PROSPECT,
        MessageClassification.BUSINESS_PARTNER,
        MessageClassification.BUSINESS_REFERRAL,
    }:
        score += 45.0
    elif primary in {
        MessageClassification.BUSINESS_NETWORK,
        MessageClassification.BUSINESS_SERVICE,
        MessageClassification.BUSINESS_VENDOR,
    }:
        score += 25.0
    elif primary == MessageClassification.BUSINESS_ADMIN:
        score += 20.0
    elif primary in {MessageClassification.EDUCATION}:
        score += 10.0
    elif primary in {MessageClassification.SOCIAL_NOTIFICATION, MessageClassification.PROMOTIONAL}:
        score -= 10.0
    if partnership:
        score += 10.0
    if meeting:
        score += 8.0
    if proposal:
        score += 10.0
    if is_client:
        score += 20.0
    if is_contacted_prospect:
        score += 15.0
    if security or system_failure:
        score += 10.0
    score = max(0.0, min(100.0, score))
    _ev(evidence, "relevance_score", f"score={score:.0f} primary={primary.value}", weight=0.9)

    # --- Founder Attention Score (0-100) ------------------------------------
    attention = 0.0
    kinds: list[str] = []

    def bump(amount: float, kind: FounderAttentionKind, signal: str, detail: str) -> None:
        nonlocal attention
        attention += amount
        kinds.append(kind.value)
        _ev(evidence, f"attention_{signal}", detail, weight=0.7)

    if security:
        bump(70.0, FounderAttentionKind.SECURITY_ISSUE, "security", "Security terminology present")
    if system_failure:
        bump(75.0, FounderAttentionKind.SYSTEM_FAILURE, "system", "System-failure terminology present")
    if QUESTION_TERMS.search(text):
        bump(55.0, FounderAttentionKind.EXPLICIT_QUESTION, "question", "Explicit question requiring an answer")
    if DELIVERABLE_TERMS.search(text):
        bump(45.0, FounderAttentionKind.REQUEST_DELIVERABLE, "deliverable", "Request for a deliverable")
    if proposal:
        bump(40.0, FounderAttentionKind.PROPOSAL_REQUEST, "proposal", "Proposal/quote language")
    if payment and primary not in {MessageClassification.TRANSACTIONAL}:
        bump(50.0, FounderAttentionKind.PAYMENT_ISSUE, "payment", "Payment/invoice language")
    if meeting:
        bump(30.0, FounderAttentionKind.MEETING_REQUEST, "meeting", "Meeting/connection language")
    if DEADLINE_TERMS.search(text):
        bump(35.0, FounderAttentionKind.DEADLINE, "deadline", "Deadline language")
    if COMMITMENT_TERMS.search(text):
        bump(25.0, FounderAttentionKind.UNRESOLVED_COMMITMENT, "commitment", "Commitment/follow-up language")
    if OBJECTION_TERMS.search(text):
        bump(25.0, FounderAttentionKind.CLIENT_PROBLEM, "objection", "Objection/problem language")
    if is_client:
        bump(20.0, FounderAttentionKind.RELATIONSHIP_FOLLOWUP, "client", "Active client follow-up")

    # Negative attention factors — these REDUCE attention demand.
    if primary == MessageClassification.PROMOTIONAL:
        attention -= 90.0
        _ev(evidence, "attention_negative", "Promotional class suppresses attention", weight=1.0)
    if primary == MessageClassification.NEWSLETTER:
        attention -= 85.0
        _ev(evidence, "attention_negative", "Newsletter class suppresses attention", weight=1.0)
    if primary == MessageClassification.SOCIAL_NOTIFICATION:
        attention -= 70.0
        _ev(evidence, "attention_negative", "Social notification suppresses attention", weight=1.0)
    if primary == MessageClassification.TRANSACTIONAL:
        attention -= 60.0
        _ev(evidence, "attention_negative", "Transactional class suppresses attention", weight=1.0)
    if primary == MessageClassification.AUTOMATED_NOTIFICATION and not (security or system_failure):
        attention -= 30.0
        _ev(evidence, "attention_negative", "Routine automated notification suppresses attention", weight=1.0)

    attention = max(0.0, min(100.0, attention))

    # Confidence reflects how decisive the signal set was.
    strength = len([e for e in evidence if e.get("weight", 0) >= 0.7])
    confidence = min(0.95, 0.35 + strength * 0.12)
    if primary in {MessageClassification.PERSONAL, MessageClassification.UNKNOWN}:
        confidence = min(confidence, 0.55)

    return ClassificationResult(
        primary=primary,
        secondary_tags=tags,
        relevance_score=round(score, 1),
        attention_score=round(attention, 1),
        attention_kinds=sorted(set(kinds)),
        confidence=round(confidence, 2),
        evidence=evidence,
        reasoning=reasoning,
        version=CLASSIFIER_VERSION,
    )
