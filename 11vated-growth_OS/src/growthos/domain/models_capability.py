"""Capability Intelligence persistence models."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from growthos.domain.base import Record, jsonb


class CapabilityCanonEvent(Record):
    """A persistent, restart-safe commercial event for the Capability Canon.

    ``CAPABILITY_CANON_CHANGED`` is the first event type. It survives restarts
    and is processed deterministically by Revenue Scout (selective prospect
    requalification) rather than relying on in-process callbacks.
    """

    __tablename__ = "capability_canon_event"

    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(80), default="CAPABILITY_CANON_CHANGED", nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CapabilityProductHypothesis(Record):
    """A product/IP/SDK/middleware hypothesis derived from a confirmed capability.

    Stored separately from Capability Canon: a hypothesis never implies a real
    Product Canon entry and never becomes externally claimable on its own.
    """

    __tablename__ = "capability_product_hypothesis"

    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hypothesis_type: Mapped[str] = mapped_column(String(40), nullable=False)  # PRODUCT_/IP_/SDK_/MIDDLEWARE_
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="HYPOTHESIS", nullable=False)


class TrustedRepositoryRoot(Record):
    __tablename__ = "trusted_repository_root"
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    founder_id: Mapped[str] = mapped_column(String(64), default="founder", nullable=False)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("path", name="uq_trusted_repository_root_path"),)


class ProjectEvidenceRecord(Record):
    __tablename__ = "project_evidence_record"
    repository_root_id: Mapped[str] = mapped_column(ForeignKey("trusted_repository_root.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    git_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    git_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    remote_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    readme_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    languages: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    manifests: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    source_directories: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    test_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_paths: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    inspected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    intelligence_profile: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    privacy_notes: Mapped[str] = mapped_column(Text, default="Source remains local; only summaries and hashes persist.", nullable=False)
    __table_args__ = (UniqueConstraint("path", name="uq_project_evidence_path"),)


class CapabilityEvidenceRecord(Record):
    __tablename__ = "capability_evidence_record"
    capability_id: Mapped[str | None] = mapped_column(ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("project_evidence_record.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_location: Mapped[str] = mapped_column(String(2048), nullable=False)
    artifact: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(80), default="DOCUMENTED_CLAIM", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sensitivity: Mapped[str] = mapped_column(String(40), default="INTERNAL", nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Provenance
    branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evidence_source: Mapped[str] = mapped_column(String(40), default="github", nullable=False)  # github / local / mixed
    # Evidence sufficiency
    files_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_inspected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_files_inspected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    test_files_inspected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    build_files_inspected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    docs_inspected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deep_review_status: Mapped[str] = mapped_column(String(40), default="NOT_REVIEWED", nullable=False)
    coverage_limitations: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    # Quality markers
    test_quality: Mapped[str | None] = mapped_column(String(60), nullable=True)
    build_quality: Mapped[str | None] = mapped_column(String(60), nullable=True)
    runtime_quality: Mapped[str | None] = mapped_column(String(60), nullable=True)
    evidence_independence: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # Semantic validation
    implementation_details: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)


class CapabilityEvidenceAttribution(Record):
    """Precise file/subsystem → capability evidence attribution.

    Replaces the coarse-grained ``related_completed_work`` approach with
    explicit per-file, per-subsystem attribution that can be audited,
    explained, and independently verified.
    """

    __tablename__ = "capability_evidence_attribution"

    capability_id: Mapped[str] = mapped_column(
        ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository: Mapped[str] = mapped_column(String(400), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    subsystem: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    attribution_directness: Mapped[str] = mapped_column(String(40), nullable=False)
    attribution_reason: Mapped[str] = mapped_column(Text, nullable=False)
    symbol_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    line_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    evidence_source: Mapped[str] = mapped_column(String(40), default="local_mirror", nullable=False)
    # Confidence that this specific file supports this specific capability
    attribution_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Whether this attribution passed test validation
    has_validating_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validating_test_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    # For test attributions: which subsystem/behavior this test validates
    validates_subsystem: Mapped[str | None] = mapped_column(String(200), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "capability_id", "repository", "file_path",
            name="uq_capability_attribution_file",
        ),
    )


class CapabilityReviewEvent(Record):
    __tablename__ = "capability_review_event"
    capability_id: Mapped[str] = mapped_column(ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_state: Mapped[str | None] = mapped_column(String(60), nullable=True)
    new_state: Mapped[str] = mapped_column(String(60), nullable=False)
    changed_fields: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_context: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    actor: Mapped[str] = mapped_column(String(120), default="founder", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProblemCanon(Record):
    __tablename__ = "problem_canon"
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    source_prospect_id: Mapped[str | None] = mapped_column(ForeignKey("prospect.id", ondelete="SET NULL"), nullable=True, index=True)
    evidence_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="hypothesis", nullable=False)
    __table_args__ = (UniqueConstraint("name", name="uq_problem_canon_name"),)


class ProblemCapabilityMatch(Record):
    __tablename__ = "problem_capability_match"
    problem_id: Mapped[str] = mapped_column(ForeignKey("problem_canon.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_id: Mapped[str] = mapped_column(ForeignKey("capability_canon.id", ondelete="CASCADE"), nullable=False, index=True)
    fit_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_complexity: Mapped[float | None] = mapped_column(Float, nullable=True)
    founder_effort: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reuse_potential: Mapped[float | None] = mapped_column(Float, nullable=True)
    limitations: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    commercial_suitability: Mapped[float | None] = mapped_column(Float, nullable=True)
    __table_args__ = (UniqueConstraint("problem_id", "capability_id", name="uq_problem_capability_match"),)


class CapabilityGap(Record):
    __tablename__ = "capability_gap"
    problem_id: Mapped[str | None] = mapped_column(ForeignKey("problem_canon.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(40), default="REVIEW", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="PROPOSED", nullable=False)


class CapabilityDemandSignal(Record):
    __tablename__ = "capability_demand_signal"
    capability_id: Mapped[str | None] = mapped_column(ForeignKey("capability_canon.id", ondelete="SET NULL"), nullable=True, index=True)
    problem_id: Mapped[str | None] = mapped_column(ForeignKey("problem_canon.id", ondelete="SET NULL"), nullable=True, index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observed_demand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class CapabilityPortfolioSnapshot(Record):
    __tablename__ = "capability_portfolio_snapshot"
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    verified_capability_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    proposed_capability_ids: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    demand_summary: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    private_source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class EvidenceMirror(Record):
    """A local read-only clone of a founder-authorized GitHub repository.

    Used only for deep source evidence analysis. Mirrors are never pushed,
    never modified, and never used as development workspaces.
    """

    __tablename__ = "evidence_mirror"

    owner: Mapped[str] = mapped_column(String(200), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(400), nullable=False, unique=True)
    remote_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    local_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fetched_refs: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    remote_commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    local_evidence_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    mirror_state: Mapped[str] = mapped_column(String(40), default="NOT_MIRRORED", nullable=False)
    is_fresh: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    authorization_source: Mapped[str] = mapped_column(String(200), default="founder_authorized", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    files_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_roots: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    languages: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    size_kb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_deep_analysis_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("full_name", name="uq_evidence_mirror_full_name"),)


class GitHubProfileEvidenceSource(Record):
    """An explicitly founder-authorized GitHub profile (read-only evidence scope).

    Authorization is explicit and per-profile; no neighboring accounts or
    repositories are discovered automatically.
    """

    __tablename__ = "github_profile_evidence_source"

    login: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    authorization_state: Mapped[str] = mapped_column(
        String(60), default="AUTHORIZED_READ_ONLY", nullable=False
    )
    visibility_state: Mapped[str] = mapped_column(String(60), default="UNSCANNED", nullable=False)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    repositories_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repositories_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("login", name="uq_github_profile_login"),)


class RepositoryEvidence(Record):
    """Lightweight first-pass evidence census of one public repository.

    Only public metadata and file-tree presence signals are recorded — no
    source is persisted. ``evidence_strength`` is an independent classification,
    not a capability claim.
    """

    __tablename__ = "repository_evidence"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("github_profile_evidence_source.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(400), nullable=False, unique=True)
    html_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    topics: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    visibility: Mapped[str] = mapped_column(String(40), default="public", nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fork: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    languages: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    size_kb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stargazers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    readme_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tests_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ci_build_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    releases_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    architecture_docs_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    empty_or_minimal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence_strength: Mapped[str] = mapped_column(
        String(60), default="EMPTY_OR_MINIMAL", nullable=False
    )
    evidence_value_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(jsonb, default=dict, nullable=False)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    family_id: Mapped[str | None] = mapped_column(
        ForeignKey("project_family.id", ondelete="SET NULL"), nullable=True, index=True
    )

    __table_args__ = (UniqueConstraint("full_name", name="uq_repository_evidence_full_name"),)


class ProjectFamily(Record):
    """A clustered lineage of repositories that likely represent one underlying
    technology family (e.g. generations/forks of the same system).

    Several repos describing the same system must not multiply company
    capability breadth; they are grouped here as one evidence family.
    """

    __tablename__ = "project_family"

    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_languages: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)
    evidence_strength: Mapped[str] = mapped_column(
        String(60), default="EMPTY_OR_MINIMAL", nullable=False
    )
    evidence_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    overlap_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    capability_candidates: Mapped[list[str]] = mapped_column(jsonb, default=list, nullable=False)

    __table_args__ = (UniqueConstraint("slug", name="uq_project_family_slug"),)
