"""System/operational entities.

These underpin auth, the persistent job system, the audit ledger, the approval
workflow, the agent action ledger, AI request provenance, and the cost guard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from growthos.domain.base import Record, jsonb
from growthos.domain.enums import (
    AgentActionStatus,
    ApprovalStatus,
    ConnectorBilling,
    IntegrationKind,
    JobState,
    PermissionDecision,
)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class Founder(Record):
    __tablename__ = "founder"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sessions: Mapped[list[Session]] = relationship(
        back_populates="founder", cascade="all, delete-orphan"
    )


class Session(Record):
    __tablename__ = "session"

    founder_id: Mapped[str] = mapped_column(
        ForeignKey("founder.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    founder: Mapped[Founder] = relationship(back_populates="sessions")


# ---------------------------------------------------------------------------
# Persistent job system
# ---------------------------------------------------------------------------


class Job(Record):
    __tablename__ = "job"

    type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    state: Mapped[JobState] = mapped_column(default=JobState.PENDING, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(jsonb, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    backoff_base_seconds: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parent_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("job.id", ondelete="SET NULL"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "type", "idempotency_key", name="uq_job_type_idempotency"
        ),
    )


# ---------------------------------------------------------------------------
# Audit and approvals
# ---------------------------------------------------------------------------


class AuditEvent(Record):
    __tablename__ = "audit_event"

    actor: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_state: Mapped[dict[str, Any] | None] = mapped_column(jsonb, nullable=True)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(jsonb, nullable=True)
    decision: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)


class Approval(Record):
    __tablename__ = "approval"

    action: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    target_entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(
        default=ApprovalStatus.REQUESTED, nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_by: Mapped[str | None] = mapped_column(String(200), nullable=True)


class AgentAction(Record):
    __tablename__ = "agent_action"

    actor: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    tool: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_evidence_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    reasoning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    decision: Mapped[PermissionDecision] = mapped_column(nullable=False)
    approval_id: Mapped[str | None] = mapped_column(
        ForeignKey("approval.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[AgentActionStatus] = mapped_column(
        default=AgentActionStatus.REQUESTED, nullable=False
    )
    previous_state: Mapped[dict[str, Any] | None] = mapped_column(jsonb, nullable=True)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(jsonb, nullable=True)
    integration: Mapped[str | None] = mapped_column(String(120), nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(jsonb, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Local AI request provenance
# ---------------------------------------------------------------------------


class ModelRequest(Record):
    __tablename__ = "model_request"

    provider: Mapped[str] = mapped_column(String(40), default="ollama", nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    input_evidence_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_output: Mapped[dict[str, Any] | None] = mapped_column(jsonb, nullable=True)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Cost guard: connector registry
# ---------------------------------------------------------------------------


class Connector(Record):
    __tablename__ = "connector"

    provider: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    kind: Mapped[IntegrationKind] = mapped_column(nullable=False)
    free_open_status: Mapped[str] = mapped_column(String(40), nullable=False)
    billing: Mapped[ConnectorBilling] = mapped_column(
        default=ConnectorBilling.FREE, nullable=False
    )
    known_limit: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_possibility: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    credential_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    policy_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    policy_block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_policy_verification: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
