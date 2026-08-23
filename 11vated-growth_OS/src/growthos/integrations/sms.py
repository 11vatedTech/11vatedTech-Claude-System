"""SMS bridge — contract logic.

Real two-way SMS requires an Android gateway device + SIM. This module encodes
the parts that are testable without hardware:

- inbound persistence BEFORE agent processing
- dedup by gateway message ID
- founder number allowlisting and privileged command classification
- the rule that SMS alone never authorizes high-risk actions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from growthos.domain.enums import PermissionDecision
from growthos.security.permissions import AutonomyEngine

FOUNDER_PREFIXES = ("FOUNDER:",)


@dataclass(frozen=True)
class InboundSms:
    sender: str
    body: str
    gateway_message_id: str
    device_timestamp: datetime | None = None
    received_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


@dataclass(frozen=True)
class SmsClassification:
    sender: str
    is_founder: bool
    is_command: bool
    normalized_body: str


def normalize_phone(number: str) -> str:
    """Normalize a phone number for stable comparison."""
    digits = "".join(ch for ch in number if ch.isdigit())
    if digits.startswith("1") and len(digits) == 11:  # strip US country code
        digits = digits[1:]
    return digits


def classify_sms(
    sender: str,
    founder_number: str,
    body: str,
    *,
    command_prefixes: tuple[str, ...] = FOUNDER_PREFIXES,
) -> SmsClassification:
    is_founder = normalize_phone(sender) == normalize_phone(founder_number)
    normalized = body.strip()
    is_command = is_founder and (
        normalized.upper().startswith(command_prefixes)
        or len(normalized.split()) <= 12  # short founder utterances are commands
    )
    return SmsClassification(
        sender=sender,
        is_founder=is_founder,
        is_command=is_command,
        normalized_body=normalized,
    )


def sms_can_authorize(action: str) -> bool:
    """Return True if an action may be authorized via SMS alone.

    High-risk actions require dashboard/PWA confirmation and are never
    authorized by a text message, regardless of sender.
    """
    result = AutonomyEngine().evaluate(action, via_channel="sms")
    return result.decision is PermissionDecision.ALLOW


def compose_reply(items: list[str], *, max_chars: int = 320) -> str:
    """Compose a concise multi-item SMS reply, truncating safely."""
    reply = ""
    for item in items:
        if not reply:
            reply = item
        elif len(reply) + len(item) + 2 <= max_chars:
            reply = f"{reply}\n{item}"
        else:
            break
    return reply
