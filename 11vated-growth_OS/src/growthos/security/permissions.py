"""Deterministic autonomy policy engine.

Every consequential tool operation resolves through:

    actor -> requested action -> target -> policy -> decision

The default policy is hard-coded, deterministic software. An LLM never decides
whether it is allowed to act.
"""

from __future__ import annotations

from dataclasses import dataclass

from growthos.domain.enums import PermissionDecision

# action -> (default decision, risk_level)
# risk_level "high" means SMS/other non-dashboard channels alone cannot approve.
ACTION_POLICIES: dict[str, tuple[PermissionDecision, str]] = {
    # --- Autonomous (AUTO) ---
    "research": (PermissionDecision.ALLOW, "low"),
    "analyze_public_website": (PermissionDecision.ALLOW, "low"),
    "classify": (PermissionDecision.ALLOW, "low"),
    "summarize": (PermissionDecision.ALLOW, "low"),
    "analyze_product": (PermissionDecision.ALLOW, "low"),
    "market_hypothesis": (PermissionDecision.ALLOW, "low"),
    "opportunity_recommendation": (PermissionDecision.ALLOW, "low"),
    "draft_email": (PermissionDecision.ALLOW, "low"),
    "draft_sms": (PermissionDecision.ALLOW, "low"),
    "draft_linkedin_message": (PermissionDecision.ALLOW, "low"),
    "update_low_risk_intelligence": (PermissionDecision.ALLOW, "low"),
    # --- Approval-controlled ---
    "send_prospect_email": (PermissionDecision.REQUIRE_APPROVAL, "medium"),
    "send_client_sms": (PermissionDecision.REQUIRE_APPROVAL, "medium"),
    "communicate_final_price": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "discount": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "commit_scope": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "promise_delivery_date": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "send_proposal": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "publish_linkedin_content": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "contractual_statement": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    # --- High-risk: dashboard-only, never SMS-only ---
    "accept_contract": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "financial_transfer": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "credential_change": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "delete_commercial_history": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    "security_configuration": (PermissionDecision.REQUIRE_APPROVAL, "high"),
    # --- Explicitly denied by default ---
    "circumvent_anti_bot": (PermissionDecision.DENY, "high"),
    "auto_connection_request": (PermissionDecision.DENY, "high"),
    "auto_bulk_dm": (PermissionDecision.DENY, "high"),
    "fake_engagement": (PermissionDecision.DENY, "high"),
    "bypass_robots_txt": (PermissionDecision.DENY, "high"),
}

DASHBOARD_ONLY_ACTIONS = {
    "accept_contract",
    "financial_transfer",
    "credential_change",
    "delete_commercial_history",
    "security_configuration",
}


@dataclass(frozen=True)
class PolicyResult:
    decision: PermissionDecision
    risk_level: str
    action: str
    via_channel: str
    reason: str | None = None


class AutonomyEngine:
    """Evaluates actions against the default autonomy policy."""

    def evaluate(self, action: str, via_channel: str = "web") -> PolicyResult:
        if action not in ACTION_POLICIES:
            # Unknown actions are denied by default (fail closed).
            return PolicyResult(
                decision=PermissionDecision.DENY,
                risk_level="high",
                action=action,
                via_channel=via_channel,
                reason=f"Unknown action {action!r}; denied by default",
            )
        decision, risk = ACTION_POLICIES[action]

        # High-risk actions require the dashboard/PWA confirmation channel.
        # A command arriving via SMS (or another non-dashboard channel) alone
        # must not authorize them.
        if action in DASHBOARD_ONLY_ACTIONS and via_channel != "web":
            return PolicyResult(
                decision=PermissionDecision.DENY,
                risk_level=risk,
                action=action,
                via_channel=via_channel,
                reason=(
                    f"Action {action!r} requires dashboard/PWA confirmation; "
                    f"{via_channel!r} alone cannot authorize it"
                ),
            )
        return PolicyResult(
            decision=decision,
            risk_level=risk,
            action=action,
            via_channel=via_channel,
        )

    def is_auto(self, action: str, via_channel: str = "web") -> bool:
        return self.evaluate(action, via_channel).decision is PermissionDecision.ALLOW


def get_autonomy_engine() -> AutonomyEngine:
    return AutonomyEngine()
