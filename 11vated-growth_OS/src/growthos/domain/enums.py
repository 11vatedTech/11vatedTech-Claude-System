"""Canonical enums.

These are the typed vocabulary of the commercial graph. They are intentionally
defined here (not in the database layer) so they can be used in Pydantic
schemas, SQLAlchemy mappings, and pure logic without import cycles.
"""

from __future__ import annotations

import enum


class StrEnum(enum.StrEnum):
    """A string enum whose values serialize cleanly to JSON and the DB."""


class TruthClass(StrEnum):
    """The four truth classes of the provenance architecture."""

    FACT = "FACT"
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"


class ClaimTag(StrEnum):
    """How a product/capability claim was established."""

    FOUNDER_FACT = "FOUNDER_FACT"
    VERIFIED_EVIDENCE = "VERIFIED_EVIDENCE"
    AGENT_INTERPRETATION = "AGENT_INTERPRETATION"
    COMMERCIAL_HYPOTHESIS = "COMMERCIAL_HYPOTHESIS"
    ASPIRATION = "ASPIRATION"


class PipelineStage(StrEnum):
    DISCOVERED = "discovered"
    RESEARCHED = "researched"
    QUALIFIED = "qualified"
    RELATIONSHIP_DEVELOPING = "relationship_developing"
    OUTREACH_READY = "outreach_ready"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    DISCOVERY = "discovery"
    SOLUTION_DEFINED = "solution_defined"
    PROPOSAL_READY = "proposal_ready"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    HANDOFF = "handoff"
    DELIVERY = "delivery"
    COMPLETED = "completed"
    EXPANSION = "expansion"
    REFERRAL = "referral"
    LOST = "lost"
    DORMANT = "dormant"


class OutreachState(StrEnum):
    DRAFT = "draft"
    NEEDS_APPROVAL = "needs_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    SENT = "sent"
    REPLIED = "replied"
    STOPPED = "stopped"
    OPTED_OUT = "opted_out"


class OpportunityClassification(StrEnum):
    PURSUE_NOW = "pursue_now"
    DEVELOP_RELATIONSHIP = "develop_relationship"
    NURTURE = "nurture"
    PARTNER = "partner"
    MONITOR = "monitor"
    REJECT = "reject"


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    VALIDATING = "validating"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ProductMaturity(StrEnum):
    IDEA = "idea"
    CONCEPT = "concept"
    PROTOTYPE = "prototype"
    WORKING_PROTOTYPE = "working_prototype"
    MVP = "mvp"
    PRODUCTION = "production"
    SCALING = "scaling"
    ARCHIVED = "archived"


class JobState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD = "dead"
    CANCELLED = "cancelled"


class ApprovalStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PermissionDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class ChannelType(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    LINKEDIN = "linkedin"
    WEB = "web"
    CALL = "call"
    MEETING = "meeting"
    OTHER = "other"


class RelationshipStage(StrEnum):
    STRANGER = "stranger"
    CONNECTION_REQUESTED = "connection_requested"
    CONNECTED = "connected"
    INTRODUCED = "introduced"
    ENGAGED = "engaged"
    CLIENT = "client"
    PARTNER = "partner"
    DORMANT = "dormant"


class RelationshipRole(StrEnum):
    POTENTIAL_CLIENT = "potential_client"
    REFERRAL_SOURCE = "referral_source"
    AGENCY_PARTNER = "agency_partner"
    WHITE_LABEL_PARTNER = "white_label_partner"
    FOUNDER_PEER = "founder_peer"
    DISTRIBUTION_PARTNER = "distribution_partner"
    DESIGNER = "designer"
    DEVELOPER = "developer"
    INVESTOR_CONNECTION = "investor_connection"
    LOCAL_BUSINESS_CONNECTOR = "local_business_connector"
    CONTENT_COLLABORATOR = "content_collaborator"
    SPECIALIST_CONTRACTOR = "specialist_contractor"
    LONG_TERM_RELATIONSHIP = "long_term_relationship"


class MessageClassification(StrEnum):
    """Primary commercial classification of an email message."""

    BUSINESS_CLIENT = "BUSINESS_CLIENT"
    BUSINESS_PROSPECT = "BUSINESS_PROSPECT"
    BUSINESS_PARTNER = "BUSINESS_PARTNER"
    BUSINESS_REFERRAL = "BUSINESS_REFERRAL"
    BUSINESS_NETWORK = "BUSINESS_NETWORK"
    BUSINESS_VENDOR = "BUSINESS_VENDOR"
    BUSINESS_SERVICE = "BUSINESS_SERVICE"
    BUSINESS_ADMIN = "BUSINESS_ADMIN"
    EDUCATION = "EDUCATION"
    PERSONAL = "PERSONAL"
    TRANSACTIONAL = "TRANSACTIONAL"
    NEWSLETTER = "NEWSLETTER"
    PROMOTIONAL = "PROMOTIONAL"
    SOCIAL_NOTIFICATION = "SOCIAL_NOTIFICATION"
    AUTOMATED_NOTIFICATION = "AUTOMATED_NOTIFICATION"
    SPAM_OR_LOW_VALUE = "SPAM_OR_LOW_VALUE"
    UNKNOWN = "UNKNOWN"


class PipelineState(StrEnum):
    """Lifecycle states of a commercial relationship in the GrowthOS pipeline.

    Founder Inbox eligibility is derived from these states, not from email
    semantics alone: an arbitrary sender (or a discovered-but-uncontacted
    prospect) is NOT inbox-eligible.
    """

    PROSPECT_DISCOVERED = "PROSPECT_DISCOVERED"
    PROSPECT_QUALIFIED = "PROSPECT_QUALIFIED"
    OUTREACH_APPROVED = "OUTREACH_APPROVED"
    OUTREACH_SENT = "OUTREACH_SENT"
    PROSPECT_CONTACTED = "PROSPECT_CONTACTED"
    PROSPECT_REPLIED = "PROSPECT_REPLIED"
    DISCOVERY_ACTIVE = "DISCOVERY_ACTIVE"
    PROPOSAL_ACTIVE = "PROPOSAL_ACTIVE"
    NEGOTIATION_ACTIVE = "NEGOTIATION_ACTIVE"
    CLIENT_ACTIVE = "CLIENT_ACTIVE"
    PARTNER_ACTIVE = "PARTNER_ACTIVE"
    FOLLOW_UP_ACTIVE = "FOLLOW_UP_ACTIVE"
    RELATIONSHIP_ARCHIVED = "RELATIONSHIP_ARCHIVED"


class FounderAttentionKind(StrEnum):
    """Why a message warrants founder attention (attention score drivers)."""

    EXPLICIT_QUESTION = "explicit_question"
    REQUEST_DELIVERABLE = "request_deliverable"
    PROPOSAL_REQUEST = "proposal_request"
    PRICING_REQUEST = "pricing_request"
    CLIENT_PROBLEM = "client_problem"
    MEETING_REQUEST = "meeting_request"
    DEADLINE = "deadline"
    CONTRACTUAL = "contractual"
    PAYMENT_ISSUE = "payment_issue"
    OPPORTUNITY_RESPONSE = "opportunity_response"
    RELATIONSHIP_FOLLOWUP = "relationship_followup"
    SECURITY_ISSUE = "security_issue"
    SYSTEM_FAILURE = "system_failure"
    UNRESOLVED_COMMITMENT = "unresolved_commitment"


class IntegrationKind(StrEnum):
    GMAIL = "gmail"
    LINKEDIN = "linkedin"
    SMS_GATEWAY = "sms_gateway"
    OLLAMA = "ollama"
    RESEARCH = "research"


class IntegrationStatus(StrEnum):
    NOT_CONFIGURED = "not_configured"
    CONFIGURED = "configured"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    FAILED = "failed"


class FounderInboxKind(StrEnum):
    EMAIL_NEEDS_RESPONSE = "email_needs_response"
    SMS_RECEIVED = "sms_received"
    DRAFT_AWAITING_APPROVAL = "draft_awaiting_approval"
    PROPOSAL_AWAITING_APPROVAL = "proposal_awaiting_approval"
    CLIENT_REQUIREMENT = "client_requirement"
    FOLLOWUP_DUE = "followup_due"
    DEADLINE_APPROACHING = "deadline_approaching"
    INTEGRATION_FAILED = "integration_failed"
    PRODUCT_VALIDATION_REQUIRED = "product_validation_required"
    OPPORTUNITY_CHANGED = "opportunity_changed"
    AGENT_NEEDS_JUDGMENT = "agent_needs_judgment"
    APPROVAL_REQUESTED = "approval_requested"


class FounderInboxStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class AgentActionStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SuppressionScope(StrEnum):
    ALL_CHANNELS = "all_channels"
    EMAIL = "email"
    SMS = "sms"
    LINKEDIN = "linkedin"
    CALL = "call"


class ConnectorBilling(StrEnum):
    FREE = "free"
    OPEN = "open"
    FREE_TIER = "free_tier"
    BILLABLE = "billable"
    CREDENTIAL_ONLY = "credential_only"


class OutboundStatus(StrEnum):
    """State of an outbound communication."""

    ALLOWED = "allowed"
    BLOCKED_SUPPRESSION = "blocked_suppression"
    BLOCKED_APPROVAL = "blocked_approval"
    BLOCKED_POLICY = "blocked_policy"
    BLOCKED_COMPLIANCE = "blocked_compliance"
    BLOCKED_KILL_SWITCH = "blocked_kill_switch"
    SENT = "sent"
    FAILED = "failed"


class ScoutMode(StrEnum):
    """Autonomy mode of the Revenue Scout.

    Default is ASSIST: the scout researches and drafts freely, but sends are
    founder-approved. CAMPAIGN_AUTO allows sends strictly within an approved
    campaign policy. FULL_RESEARCH increases discovery aggressiveness while
    keeping the communication policy separate.
    """

    OBSERVE = "observe"  # discover/research only, never outreach
    ASSIST = "assist"  # discover/research/draft; founder approves sends
    CAMPAIGN_AUTO = "campaign_auto"  # approved campaigns may send in-policy
    FULL_RESEARCH = "full_research"  # aggressive discovery; comms policy unchanged


class CapabilityProposalState(StrEnum):
    DISCOVERED = "DISCOVERED"
    EVIDENCE_GATHERING = "EVIDENCE_GATHERING"
    PROPOSED = "PROPOSED"
    FOUNDER_CONFIRMED = "FOUNDER_CONFIRMED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    RESTRICTED = "RESTRICTED"
    RETIRED = "RETIRED"


class DeliveryMaturity(StrEnum):
    EXPERIMENTAL = "EXPERIMENTAL"
    PROTOTYPE_PROVEN = "PROTOTYPE_PROVEN"
    INTERNAL_PROVEN = "INTERNAL_PROVEN"
    CLIENT_READY = "CLIENT_READY"
    PRODUCTION_PROVEN = "PRODUCTION_PROVEN"


class CapabilityStatus(StrEnum):
    PROPOSED = "PROPOSED"
    FOUNDER_CONFIRMED = "FOUNDER_CONFIRMED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    RESTRICTED = "RESTRICTED"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"  # founder-level rejection; not auto-generated
    WITHHELD_BY_CRITIC = "WITHHELD_BY_CRITIC"  # agent recommends withholding
    SUPERSEDED = "SUPERSEDED"  # replaced by a better capability candidate
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"  # evidence not sufficient for any decision


class DeepReviewStatus(StrEnum):
    """Tracks whether a repository has received sufficient deep evidence analysis."""
    NOT_REVIEWED = "NOT_REVIEWED"
    COMPLETE = "DEEP_REVIEW_COMPLETE"
    PARTIAL = "DEEP_REVIEW_PARTIAL"
    INSUFFICIENT = "DEEP_REVIEW_INSUFFICIENT"
    RATE_LIMITED = "DEEP_REVIEW_RATE_LIMITED"
    BLOCKED = "DEEP_REVIEW_BLOCKED"


class EvidenceQuality(StrEnum):
    """Semantic evidence quality markers for tests, build, and runtime."""
    # Test evidence
    TEST_FILES_PRESENT = "TEST_FILES_PRESENT"
    TESTS_DISCOVERED = "TESTS_DISCOVERED"
    TESTS_EXECUTED = "TESTS_EXECUTED"
    TESTS_PASSING = "TESTS_PASSING"
    INTEGRATION_TESTS_PASSING = "INTEGRATION_TESTS_PASSING"
    SYSTEM_TESTS_PASSING = "SYSTEM_TESTS_PASSING"
    # Build evidence
    BUILD_CONFIG_PRESENT = "BUILD_CONFIG_PRESENT"
    BUILD_ATTEMPTED = "BUILD_ATTEMPTED"
    BUILD_VERIFIED = "BUILD_VERIFIED"
    BUILD_ARTIFACT_VERIFIED = "BUILD_ARTIFACT_VERIFIED"
    # Runtime evidence
    RUNTIME_ENTRYPOINT_PRESENT = "RUNTIME_ENTRYPOINT_PRESENT"
    RUNTIME_ATTEMPTED = "RUNTIME_ATTEMPTED"
    RUNTIME_VERIFIED = "RUNTIME_VERIFIED"
    RUNTIME_PARTIAL = "RUNTIME_PARTIAL"
    RUNTIME_BLOCKED = "RUNTIME_BLOCKED"
    STATIC_ONLY = "STATIC_ONLY"


class EvidenceIndependence(StrEnum):
    """How independent one evidence source is from another."""
    INDEPENDENT_IMPLEMENTATION = "INDEPENDENT_IMPLEMENTATION"
    SHARED_LINEAGE = "SHARED_LINEAGE"
    DERIVED_IMPLEMENTATION = "DERIVED_IMPLEMENTATION"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    DUPLICATE_EVIDENCE = "DUPLICATE_EVIDENCE"


class CommercialOfferStatus(StrEnum):
    HYPOTHESIS = "HYPOTHESIS"
    VALIDATION_READY = "VALIDATION_READY"
    VALIDATED = "VALIDATED"
    RETIRED = "RETIRED"


class ContactRouteKind(StrEnum):
    VERIFIED_BUSINESS_EMAIL = "VERIFIED_BUSINESS_EMAIL"
    VERIFIED_GENERAL_CONTACT = "VERIFIED_GENERAL_CONTACT"
    VERIFIED_PUBLIC_PHONE = "VERIFIED_PUBLIC_PHONE"
    VERIFIED_CONTACT_FORM = "VERIFIED_CONTACT_FORM"
    FOUNDER_NETWORK = "FOUNDER_NETWORK"
    UNVERIFIED_CONTACT_HYPOTHESIS = "UNVERIFIED_CONTACT_HYPOTHESIS"


class ScoutProspectState(StrEnum):
    """Evidence-gated autonomous acquisition lifecycle.

    Discovery is not qualification. Every advancement toward outreach requires
    explicit evidence and is recorded as a ProspectEvent.
    """

    DISCOVERED = "discovered"
    ENRICHMENT_REQUIRED = "enrichment_required"
    RESEARCHING = "researching"
    RESEARCHED = "researched"
    PROBLEM_EVIDENCE_FOUND = "problem_evidence_found"
    CAPABILITY_MATCHED = "capability_matched"
    OFFER_DEFINED = "offer_defined"
    CONTACT_PATH_VERIFIED = "contact_path_verified"
    SALES_QUALIFIED = "sales_qualified"
    READY_TO_CONTACT = "ready_to_contact"
    QUALIFIED = "qualified"  # legacy compatibility; not outreach-eligible
    REJECTED = "rejected"
    OUTREACH_DRAFTED = "outreach_drafted"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    CONTACTED = "contacted"
    REPLIED = "replied"
    ENGAGED = "engaged"
    DISCOVERY_ACTIVE = "discovery_active"
    OPPORTUNITY_ACTIVE = "opportunity_active"
    PROPOSAL_ACTIVE = "proposal_active"
    NEGOTIATION_ACTIVE = "negotiation_active"
    WON = "won"
    LOST = "lost"
    NURTURE = "nurture"
    PARTNER_TRACK = "partner_track"
    ARCHIVED = "archived"
    # Reclassified from a Prospect into a DiscoveryCandidate. Retained for
    # provenance; NOT counted as a commercial prospect in the funnel.
    RECLASSIFIED_AS_CANDIDATE = "reclassified_as_candidate"


class ScoutReplyClass(StrEnum):
    """Classification of a prospect reply."""

    POSITIVE_INTEREST = "positive_interest"
    QUESTION = "question"
    OBJECTION = "objection"
    NOT_NOW = "not_now"
    REFERRAL = "referral"
    WRONG_PERSON = "wrong_person"
    OPT_OUT = "opt_out"
    NEGATIVE = "negative"
    MEETING_REQUEST = "meeting_request"
    PRICING_REQUEST = "pricing_request"
    OTHER = "other"


class ResearchTruth(StrEnum):
    """Confidence tag for scout research observations."""

    VERIFIED_FACT = "verified_fact"
    DIRECT_OBSERVATION = "direct_observation"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"


class MarketThesisStatus(StrEnum):
    HYPOTHESIS = "hypothesis"
    VALIDATING = "validating"
    ACTIVE = "active"
    DORMANT = "dormant"
    REJECTED = "rejected"


class ProspectSourceKind(StrEnum):
    OVERPASS = "overpass"
    WEBSITE_AUDIT = "website_audit"
    WEB_SEARCH = "web_search"
    GMAIL = "gmail"
    LINKEDIN_IMPORT = "linkedin_import"
    FOUNDER_IMPORT = "founder_import"
    REFERRAL = "referral"
    MANUAL = "manual"
    OTHER = "other"


class OutreachBlockReason(StrEnum):
    COMPLIANCE_NOT_CONFIGURED = "OUTBOUND_MARKETING_BLOCKED"
    CAMPAIGN_POLICY = "DENIED_BY_CAMPAIGN_POLICY"
    SUPPRESSED = "SUPPRESSED"
    KILL_SWITCH = "KILL_SWITCH"
    MODE_OBSERVE = "MODE_OBSERVE"
    MODE_ASSIST = "MODE_ASSIST"
    NO_CONTACT_PATH = "NO_CONTACT_PATH"
    NOT_QUALIFIED = "NOT_QUALIFIED"


class DiscoveryCandidateState(StrEnum):
    """Pre-prospect lifecycle of an externally observed entity/signal.

    Discovery is not qualification. A candidate must pass every gate before it
    may be promoted into a real commercial Prospect.
    """

    DISCOVERED_SIGNAL = "discovered_signal"
    IDENTITY_RESOLUTION = "identity_resolution"
    ENTITY_VERIFIED = "entity_verified"
    COMMERCIAL_STATUS_CHECK = "commercial_status_check"
    MARKET_FIT_CHECK = "market_fit_check"
    PROBLEM_RESEARCH = "problem_research"
    PROSPECT_ELIGIBLE = "prospect_eligible"
    PROSPECT_CREATED = "prospect_created"
    REJECTED = "rejected"
    NOT_COMMERCIAL = "not_commercial"
    NURTURE = "nurture"


class OrganizationType(StrEnum):
    """Most defensible entity type given public evidence.

    GitHub's account type alone never implies a commercial company; these are
    resolved from corroborating public signals only.
    """

    COMMERCIAL_COMPANY = "commercial_company"
    GAME_STUDIO = "game_studio"
    AGENCY = "agency"
    INDEPENDENT_DEVELOPER = "independent_developer"
    OPEN_SOURCE_ORGANIZATION = "open_source_organization"
    INDIVIDUAL = "individual"
    HOBBY_PROJECT = "hobby_project"
    EDUCATIONAL_PROJECT = "educational_project"
    COMMUNITY_PROJECT = "community_project"
    ABANDONED_PROJECT = "abandoned_project"
    UNKNOWN = "unknown"


class ActivityStatus(StrEnum):
    ACTIVE = "active"
    LIKELY_ACTIVE = "likely_active"
    STALE = "stale"
    LIKELY_INACTIVE = "likely_inactive"
    UNKNOWN = "unknown"


class CommercialEntityStatus(StrEnum):
    """Commercial-actor gate. GitHub is not a commercial identity authority."""

    COMMERCIAL_VERIFIED = "commercial_verified"
    COMMERCIAL_UNVERIFIED = "commercial_unverified"
    NON_COMMERCIAL = "non_commercial"


class NeedEvidenceClass(StrEnum):
    """Strength of public evidence that a candidate has a need we can address."""

    DIRECT_NEED_SIGNAL = "direct_need_signal"
    STRONG_TECHNICAL_SIGNAL = "strong_technical_signal"
    INDIRECT_NEED_SIGNAL = "indirect_need_signal"
    GENERAL_RELEVANCE = "general_relevance"
    NO_NEED_EVIDENCE = "no_need_evidence"


class PurchasingCapacity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EntityTrack(StrEnum):
    """How an entity fits GrowthOS commercially (if at all)."""

    DIRECT_CLIENT_TRACK = "direct_client_track"
    PARTNER_TRACK = "partner_track"
    ECOSYSTEM_TRACK = "ecosystem_track"
    NOT_COMMERCIAL = "not_commercial"


class ContactPathClass(StrEnum):
    """Attributable public contact route classification (candidate stage)."""

    VERIFIED_BUSINESS_EMAIL = "VERIFIED_BUSINESS_EMAIL"
    VERIFIED_CONTACT_FORM = "VERIFIED_CONTACT_FORM"
    VERIFIED_PUBLIC_BUSINESS_CHANNEL = "VERIFIED_PUBLIC_BUSINESS_CHANNEL"
    FOUNDER_NETWORK = "FOUNDER_NETWORK"
    NO_VERIFIED_CONTACT = "NO_VERIFIED_CONTACT"


class RepositoryEvidenceStrength(StrEnum):
    """Independent evidence-strength classification of a repository.

    Repository existence is not capability proof. A README claim is not
    implementation proof. These levels keep that distinction explicit.
    """

    EMPTY_OR_MINIMAL = "EMPTY_OR_MINIMAL"
    DOCUMENTATION_ONLY = "DOCUMENTATION_ONLY"
    EXPERIMENTAL = "EXPERIMENTAL"
    IMPLEMENTATION_PRESENT = "IMPLEMENTATION_PRESENT"
    TEST_EVIDENCE_PRESENT = "TEST_EVIDENCE_PRESENT"
    BUILD_EVIDENCE_PRESENT = "BUILD_EVIDENCE_PRESENT"
    RUNTIME_EVIDENCE_PRESENT = "RUNTIME_EVIDENCE_PRESENT"
    STRONG_CAPABILITY_EVIDENCE = "STRONG_CAPABILITY_EVIDENCE"


class MirrorState(StrEnum):
    """Lifecycle states of a local evidence mirror clone."""
    NOT_MIRRORED = "NOT_MIRRORED"
    CLONING = "CLONING"
    READY = "READY"
    STALE = "STALE"
    FETCH_FAILED = "FETCH_FAILED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    REMOTE_UNAVAILABLE = "REMOTE_UNAVAILABLE"
    CORRUPT = "CORRUPT"


class DeepLocalAnalysisStatus(StrEnum):
    """Status of a local semantic analysis pass against a mirror."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class GitHubProfileAuthorization(StrEnum):
    """Authorization state of an explicitly-authorized GitHub profile."""

    AUTHORIZED_READ_ONLY = "AUTHORIZED_READ_ONLY"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    REVOKED = "REVOKED"


class AttributionDirectness(StrEnum):
    """How directly a file/subsystem evidence item supports a capability.

    Only DIRECT_CORE and defensible DIRECT_SUPPORTING should materially
    increase capability implementation confidence.
    """

    DIRECT_CORE = "DIRECT_CORE"  # core implementation of the capability's primary behavior
    DIRECT_SUPPORTING = "DIRECT_SUPPORTING"  # supports core behavior but is not the primary implementation
    INDIRECT_SUPPORTING = "INDIRECT_SUPPORTING"  # related but does not directly implement capability behavior
    CONTEXT_ONLY = "CONTEXT_ONLY"  # provides context (build config, docs) but no implementation evidence
    NOT_RELEVANT = "NOT_RELEVANT"  # does not support this capability at all


class CapabilityEvidenceType(StrEnum):
    """What kind of evidence an attribution represents."""

    SUBSYSTEM_IMPLEMENTATION = "SUBSYSTEM_IMPLEMENTATION"  # code implementing a detected subsystem
    FILE_IMPLEMENTATION = "FILE_IMPLEMENTATION"  # individual file with implementation signals
    TEST_VALIDATION = "TEST_VALIDATION"  # test that validates attributed behavior
    BUILD_EVIDENCE = "BUILD_EVIDENCE"  # build config or artifact
    RUNTIME_EVIDENCE = "RUNTIME_EVIDENCE"  # runtime entrypoint or execution proof
    DOCUMENTATION = "DOCUMENTATION"  # docs describing the capability
    ARCHITECTURE_SIGNAL = "ARCHITECTURE_SIGNAL"  # architectural pattern supporting the capability
