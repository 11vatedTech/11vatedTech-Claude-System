const BASE = "/api/v1";

function getCookie(name: string): string {
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : "";
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const mutating = !["GET", "HEAD", "OPTIONS"].includes(method);
  if (mutating) {
    const csrf = getCookie("growthos_csrf");
    if (csrf) headers["X-CSRF-Token"] = csrf;
  }

  const response = await fetch(BASE + path, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

  if (response.status === 401 && !path.startsWith("/auth/")) {
    window.dispatchEvent(new Event("growthos:unauthorized"));
    throw new ApiError(401, "Not authenticated");
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ")
      : (detail ?? response.statusText);
    throw new ApiError(response.status, message);
  }
  return data as T;
}

export async function ensureCsrf(): Promise<void> {
  if (!getCookie("growthos_csrf")) {
    try {
      await fetch("/api/v1/auth/csrf", { credentials: "include" });
    } catch {
      /* server not up yet */
    }
  }
}

export interface HealthState {
  prospects: number;
  opportunities: number;
  campaigns: number;
  products: number;
  people: number;
  companies: number;
  evidence: number;
  messages: number;
  revenue_events: number;
}

export interface RevenueMetrics {
  pipeline_value: string;
  weighted_pipeline: string;
  booked_revenue: string;
  collected_revenue: string;
  active_opportunities: number;
  won_opportunities: number;
  has_sufficient_data: boolean;
}

export interface Product {
  id: string;
  name: string;
  codename: string | null;
  definition: string | null;
  description: string | null;
  core_problem: string | null;
  core_insight: string | null;
  maturity: string | null;
  status: string;
  positioning: string | null;
  founder_involvement: string | null;
  features: string[];
  capabilities: string[];
  value_propositions: string[];
  target_customers: string[];
  industries: string[];
  created_at: string;
  updated_at: string;
  canon?: {
    roadmap: string[];
    features: string[];
    capabilities: string[];
    technical_differentiators: string[];
    creative_differentiators: string[];
    value_propositions: string[];
    customer_outcomes: string[];
    use_cases: string[];
    target_customers: string[];
    buyers: string[];
    partners: string[];
    industries: string[];
    commercial_models: string[];
    pricing_hypotheses: Record<string, unknown>[];
    competitive_alternatives: string[];
    delivery_requirements: string[];
    marketing_assets: string[];
    sales_assets: string[];
    objections: string[];
    limitations: string[];
    risks: string[];
    claims: Record<string, unknown>[];
    [k: string]: unknown;
  };
}

export interface PricingHypothesis {
  label: string;
  model?: string;
  target_price?: number | null;
  range?: [number, number] | null;
  floor_hypothesis?: number | null;
  premium_configuration?: string | null;
  entry_offer?: string | null;
  recurring_component?: string | null;
  confidence?: number;
  reasoning?: string;
  [k: string]: unknown;
}

export interface ProductIntelligence {
  market_map: {
    primary_market_hypothesis: string | null;
    secondary_markets: string[];
    emerging_applications: string[];
    ideal_customer_profiles: string[];
    buyer_roles: string[];
    truth_class: string;
    evidence_gap_note?: string;
    [k: string]: unknown;
  };
  sales_readiness: {
    overall: number;
    components: Record<string, { score: number; confidence: number; reasoning: string; evidence: string[] }>;
    [k: string]: unknown;
  };
  pricing: {
    hypotheses: PricingHypothesis[];
    truth_class: string;
    [k: string]: unknown;
  };
  commercial_models: { analysis: { model: string; fit: string; notes: string }[]; [k: string]: unknown };
  product: { id: string; name: string; maturity: string | null };
}

export interface ProductVersion {
  version: number;
  change_summary: string;
  created_by: string;
  created_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  product_id: string;
  objective: string | null;
  revenue_objective: string | null;
  buyer: string | null;
  offer: string | null;
  channels: string[];
  status: string;
  created_at: string;
}

export interface Opportunity {
  id: string;
  title: string;
  stage: string;
  estimated_value: string | null;
  probability: number;
  classification: string | null;
  confidence: number;
  next_action: string | null;
  created_at: string;
}

export interface InboxItem {
  id: string;
  kind: string;
  title: string;
  summary: string | null;
  status: string;
  priority: number;
  due_at: string | null;
  created_at: string;
  payload: Record<string, unknown>;
}

export interface Job {
  id: string;
  type: string;
  state: string;
  attempts: number;
  max_attempts: number;
  scheduled_at: string | null;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface ScoutControl {
  enabled: boolean;
  mode: string;
  kill_switch: boolean;
  daily_research_budget: number;
  daily_prospect_target: number;
  daily_outreach_cap: number;
  geographies: string[];
  excluded_industries: string[];
  approved_offers: string[];
  allowed_campaign_ids: string[];
  research_depth: string;
  quiet_hours: Record<string, unknown>;
  min_revenue_score: number;
  min_evidence_confidence: number;
  explore_exploit: number;
  explore_adjacent: number;
  explore_experimental: number;
  business_postal_address: string | null;
  opt_out_email: string | null;
}

export interface ScoutFunnel {
  discovered: number;
  researched: number;
  evidence_found: number;
  offer_matched: number;
  sales_qualified: number;
  ready_to_contact: number;
  contacted: number;
  replies: number;
  proposal_ready: number;
  won_clients: number;
  partner_track: number;
  nurture: number;
  total: number;
  rejected: number;
  archived: number;
}

export interface ScoutCompliance {
  outbound_marketing_allowed: boolean;
  business_postal_address_configured: boolean;
  opt_out_mechanism_configured: boolean;
  block_reason: string | null;
}

export interface ScoutBrief {
  generated_at: string;
  mode: string;
  kill_switch: boolean;
  funnel: ScoutFunnel;
  pipeline_value: number;
  recommended_actions: string[];
}

export interface ScoutOverview {
  control: ScoutControl;
  funnel: ScoutFunnel;
  compliance: ScoutCompliance;
  brief: ScoutBrief;
}

export interface ScoutProspect {
  id: string;
  status: string;
  source: string;
  company: string | null;
  company_id: string | null;
  domain: string | null;
  website: string | null;
  industry: string | null;
  location: string | null;
  contact_email: string | null;
  contact_name: string | null;
  evidence: string | null;
  revenue_score: number | null;
  short_term_score: number | null;
  strategic_score: number | null;
  probability: number | null;
  confidence: number | null;
  identity_confidence: number | null;
  problem_confidence: number | null;
  capability_fit_confidence: number | null;
  buyer_confidence: number | null;
  outreach_readiness_confidence: number | null;
  confidence_reasoning: Record<string, string>;
  qualification: Record<string, unknown>;
  expected_min: number | null;
  expected_max: number | null;
  recommended_motion: string | null;
  recommended_next: string | null;
  reasoning: string | null;
  created_at: string;
}

export interface ScoutCapability {
  id: string;
  name: string;
  definition: string;
  category: string | null;
  delivery_form: string | null;
  status: string;
  external_claimable: boolean;
  proof_evidence: Record<string, unknown>[];
  typical_customer_problem: string | null;
  deliverables: string[];
  limitations: string[];
  price_range_hypothesis: Record<string, unknown>;
  founder_review_note: string | null;
  source_evidence_ids: string[];
  maturity?: string | null;
  external_summary?: string | null;
  commercial_models?: { model: string; fit: string; notes: string }[];
}

export interface CapabilityActivationState {
  capability: {
    id: string;
    name: string;
    definition: string;
    status: string;
    external_claimable: boolean;
    maturity: string | null;
    external_summary: string | null;
    limitations: string[];
    commercial_models: { model: string; fit: string; notes: string }[];
    founder_review_note: string | null;
  };
  problem_graph: { problem: string; capability: string; fit_confidence: number; reasoning: string }[];
  problem_canon: { id: string; name: string; status: string }[];
  offers: {
    id: string; name: string; buyer: string; problem: string; deliverable: string;
    status: string; timeline_hypothesis: string | null; price_hypothesis: Record<string, unknown>;
    delivery_model: string | null; risks: string[]; exclusions: string[];
  }[];
  product_hypotheses: { id: string; hypothesis_type: string; name: string; rationale: string; status: string }[];
  market_theses: {
    id: string; market: string; buyer: string | null; problem: string | null;
    score: number; short_term_score: number; strategic_score: number; confidence: number;
    status: string; selection_reasoning: string | null; discovery_source: string | null;
  }[];
  events: { id: string; event_type: string; status: string; occurred_at: string; payload: Record<string, unknown> }[];
  outbound: string;
}

export interface ScoutOffer {
  id: string;
  name: string;
  buyer: string;
  problem: string;
  deliverable: string;
  included_capability_ids: string[];
  expected_outcome: string | null;
  delivery_model: string | null;
  timeline_hypothesis: string | null;
  price_hypothesis: Record<string, unknown>;
  status: string;
  entry_offer: string | null;
  premium_offer: string | null;
  recurring_component: string | null;
  scope_boundaries: string[];
  proof_required: string[];
  exclusions: string[];
  risks: string[];
}

export interface ScoutCandidate {
  id: string;
  canonical_name: string;
  source: string;
  state: string;
  entity_type: string;
  commercial_status: string;
  activity_status: string;
  need_evidence_class: string;
  purchasing_capacity: string;
  track: string;
  official_website: string | null;
  country_region: string | null;
  identity_confidence: number;
  commercial_entity_confidence: number;
  market_fit_confidence: number;
  buyer_potential_confidence: number;
  discovery_priority_score: number;
  problem_evidence: string | null;
  contact_paths: Record<string, unknown>[];
  decision_maker_evidence: Record<string, unknown>[];
  qualification_outcome: string | null;
  legacy_prospect_id: string | null;
  prospect_id: string | null;
}

export interface CandidateFunnel {
  candidates: number;
  identity_resolved: number;
  verified_commercial_entities: number;
  commercial_unverified: number;
  not_commercial: number;
  rejected: number;
  promoted_to_prospect: number;
}

export interface ScoutMarket {
  id: string;
  market: string;
  buyer: string | null;
  problem: string | null;
  solution: string | null;
  commercial_model: string | null;
  expected_deal_min: number | null;
  expected_deal_max: number | null;
  sales_cycle: string | null;
  margin: number | null;
  score: number;
  confidence: number;
  status: string;
  evidence_summary: string | null;
}
