"""Cost guard enforcing the FREE_RUNTIME_POLICY.

The system refuses to silently activate a billable dependency. Any feature that
requires payment surfaces ``BLOCKED_BY_FREE_RUNTIME_POLICY`` with an
explanation rather than attaching a credit card.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import ConnectorBilling
from growthos.domain.models_system import Connector
from growthos.shared.errors import PermissionDeniedError

POLICY_PATH = Path("FREE_RUNTIME_POLICY.json")

# Default connector policy: what is allowed under the free/local-first runtime.
DEFAULT_CONNECTOR_POLICY: dict[str, dict] = {
    "ollama": {"billing": "open", "allowed": True},
    "postgresql": {"billing": "open", "allowed": True},
    "gmail_api": {"billing": "free_tier", "allowed": True, "limit": "Google Workspace quotas; no paid AI/API"},
    "linkedin_api": {"billing": "credential_only", "allowed": True, "limit": "Official API products only"},
    "android_sms_gateway": {"billing": "open", "allowed": True, "limit": "Carrier SIM remains the transport"},
    "tailscale": {"billing": "free_tier", "allowed": True, "limit": "Personal/individual free plan"},
    # Billable telephony/email SaaS are blocked by policy.
    "twilio": {"billing": "billable", "allowed": False},
    "vonage": {"billing": "billable", "allowed": False},
    "messagebird": {"billing": "billable", "allowed": False},
    "sendgrid": {"billing": "billable", "allowed": False},
}


class CostGuard:
    """Enforce the machine-readable free-runtime policy."""

    def __init__(self, policy_path: Path = POLICY_PATH) -> None:
        self._policy_path = policy_path
        self._policy = self._load()

    def _load(self) -> dict:
        if self._policy_path.exists():
            try:
                data = json.loads(self._policy_path.read_text(encoding="utf-8"))
                return data.get("connectors", DEFAULT_CONNECTOR_POLICY)
            except Exception:  # noqa: BLE001
                return DEFAULT_CONNECTOR_POLICY
        return DEFAULT_CONNECTOR_POLICY

    def ensure_allowed(self, provider: str) -> None:
        """Raise ``PermissionDeniedError`` if the provider is policy-blocked."""
        policy = self._policy.get(provider)
        if policy is not None and policy.get("allowed") is False:
            raise PermissionDeniedError(
                "BLOCKED_BY_FREE_RUNTIME_POLICY: "
                f"connector {provider!r} is billable and not allowed under the "
                "free/local-first runtime policy"
            )

    def is_allowed(self, provider: str) -> bool:
        policy = self._policy.get(provider)
        if policy is None:
            # Unknown providers are blocked by default (fail closed).
            return False
        return bool(policy.get("allowed", False))

    async def register_connector(
        self, session: AsyncSession, *, provider: str, **fields
    ) -> Connector:
        """Record a connector's policy status in the database."""
        result = await session.execute(
            select(Connector).where(Connector.provider == provider)
        )
        connector = result.scalar_one_or_none()
        policy = self._policy.get(provider, {})
        billing = fields.get("billing") or policy.get("billing") or "free"
        allowed = self.is_allowed(provider)
        if connector is None:
            connector = Connector(
                provider=provider,
                kind=fields.get("kind", "research"),
                free_open_status=fields.get("free_open_status", "unknown"),
                billing=ConnectorBilling(str(billing)),
                known_limit=policy.get("limit"),
                billing_possibility=billing in {"billable", "free_tier"},
                policy_allowed=allowed,
                policy_block_reason=None if allowed else "billable connector blocked",
                credential_type=fields.get("credential_type"),
            )
            session.add(connector)
        else:
            connector.policy_allowed = allowed
            connector.billing = ConnectorBilling(str(billing))
            connector.known_limit = policy.get("limit")
            connector.policy_block_reason = None if allowed else "billable connector blocked"
        await session.flush()
        return connector


def get_cost_guard() -> CostGuard:
    return CostGuard()
