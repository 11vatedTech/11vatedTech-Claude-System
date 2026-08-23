import { useEffect, useState } from "react";
import {
  api,
  CandidateFunnel,
  ScoutCandidate,
  ScoutFunnel,
  ScoutMarket,
  ScoutOverview,
  ScoutProspect,
  ScoutCapability,
  ScoutOffer,
} from "../api";

const FUNNEL_ORDER: { key: keyof ScoutFunnel; label: string; hint: string }[] = [
  { key: "discovered", label: "Discovered", hint: "Real organizations needing enrichment; not sales-ready." },
  { key: "researched", label: "Researched", hint: "Public reconnaissance completed." },
  { key: "evidence_found", label: "Evidence Found", hint: "Defensible problem evidence, not generic category fit." },
  { key: "offer_matched", label: "Offer Matched", hint: "Approved capability and grounded offer path." },
  { key: "sales_qualified", label: "Sales Qualified", hint: "All deterministic qualification gates passed." },
  { key: "ready_to_contact", label: "Ready to Contact", hint: "Fully qualified and awaiting founder review." },
  { key: "contacted", label: "Contacted", hint: "Real prospects GrowthOS has actually contacted." },
  { key: "replies", label: "Replies", hint: "Real prospects who responded." },
  { key: "proposal_ready", label: "Proposal Ready", hint: "Opportunities requiring proposal/action." },
  { key: "won_clients", label: "Won Clients", hint: "Only actual won engagements." },
  { key: "partner_track", label: "Partner Track", hint: "Companies better served as partners." },
  { key: "nurture", label: "Nurture", hint: "Keep warm; not ready now." },
];

export function Scout() {
  const [overview, setOverview] = useState<ScoutOverview | null>(null);
  const [prospects, setProspects] = useState<ScoutProspect[]>([]);
  const [candidates, setCandidates] = useState<ScoutCandidate[]>([]);
  const [candidateFunnel, setCandidateFunnel] = useState<CandidateFunnel | null>(null);
  const [markets, setMarkets] = useState<ScoutMarket[]>([]);
  const [capabilities, setCapabilities] = useState<ScoutCapability[]>([]);
  const [offers, setOffers] = useState<ScoutOffer[]>([]);
  const [capabilityName, setCapabilityName] = useState("");
  const [capabilityDefinition, setCapabilityDefinition] = useState("");
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  const load = () => {
    api<ScoutOverview>("/scout/overview").then(setOverview).catch((e) => setError(e.message));
    api<{ prospects: ScoutProspect[] }>("/scout/prospects")
      .then((r) => setProspects(r.prospects))
      .catch(() => {});
    api<{ markets: ScoutMarket[] }>("/scout/markets")
      .then((r) => setMarkets(r.markets))
      .catch(() => {});
    api<{ capabilities: ScoutCapability[] }>("/scout/capabilities")
      .then((r) => setCapabilities(r.capabilities))
      .catch(() => {});
    api<{ offers: ScoutOffer[] }>("/scout/offers")
      .then((r) => setOffers(r.offers))
      .catch(() => {});
    api<{ candidates: ScoutCandidate[]; funnel: CandidateFunnel }>("/scout/candidates")
      .then((r) => {
        setCandidates(r.candidates);
        setCandidateFunnel(r.funnel);
      })
      .catch(() => {});
  };

  useEffect(() => {
    load();
  }, []);

  const toggleKillSwitch = async () => {
    if (!overview) return;
    try {
      await api("/scout/controls", {
        method: "PATCH",
        body: JSON.stringify({ kill_switch: !overview.control.kill_switch }),
      });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    }
  };

  const proposeCapability = async () => {
    if (!capabilityName.trim() || !capabilityDefinition.trim()) return;
    try {
      await api("/scout/capabilities", {
        method: "POST",
        body: JSON.stringify({ name: capabilityName, definition: capabilityDefinition }),
      });
      setCapabilityName("");
      setCapabilityDefinition("");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    }
  };

  const reviewCapability = async (capability: ScoutCapability, status: string) => {
    try {
      await api(`/scout/capabilities/${capability.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status, note: "Founder reviewed in Capability Review" }),
      });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    }
  };

  const runNow = async () => {
    setRunning(true);
    setError("");
    try {
      await api("/scout/run", { method: "POST" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    } finally {
      setRunning(false);
    }
  };

  const reclassifyAndEnrich = async () => {
    setRunning(true);
    setError("");
    try {
      await api("/scout/candidates/reclassify", { method: "POST" });
      await api("/scout/candidates/enrich", { method: "POST" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed");
    } finally {
      setRunning(false);
    }
  };

  if (!overview) {
    return (
      <div className="page">
        <h1>Revenue Scout</h1>
        {error && <div className="error">{error}</div>}
        <div className="boot">Loading scout…</div>
      </div>
    );
  }

  const { funnel, control, compliance, brief } = overview;

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <h1 style={{ marginBottom: 0 }}>Revenue Scout</h1>
          <p className="muted">
            Autonomous discovery → real prospects → controlled outreach. No prospect
            is called a client before a real won engagement.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="ghost" onClick={runNow} disabled={running}>
            {running ? "Scouting…" : "Run discovery now"}
          </button>
          <button
            className={control.kill_switch ? "primary" : "ghost"}
            onClick={toggleKillSwitch}
            style={control.kill_switch ? { background: "#dc2626", borderColor: "#dc2626" } : {}}
          >
            {control.kill_switch ? "KILL SWITCH ON" : "Kill switch"}
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {!compliance.outbound_marketing_allowed && (
        <div className="card" style={{ borderLeft: "3px solid var(--danger, #dc2626)" }}>
          <strong>{compliance.block_reason}</strong>
          <p className="muted" style={{ margin: 0 }}>
            Outbound marketing is blocked until a valid business postal address and
            opt-out mechanism are configured. Configure both under Settings → Revenue Scout.
          </p>
        </div>
      )}

      <div className="card" style={{ marginTop: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>Founder brief</strong>{" "}
            <span className="muted" style={{ fontSize: 12 }}>
              ({new Date(brief.generated_at).toLocaleString()}) · mode{" "}
              <span className="mono">{brief.mode}</span> · pipeline value ${brief.pipeline_value.toLocaleString()}
            </span>
          </div>
        </div>
        <ul style={{ paddingLeft: 18, color: "var(--text-dim)", margin: "8px 0 0" }}>
          {brief.recommended_actions.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      </div>

      <div className="grid grid-4" style={{ margin: "18px 0" }}>
        {FUNNEL_ORDER.map((f) => (
          <div className="card" key={f.key} style={{ margin: 0 }}>
            <div style={{ fontSize: 26, fontWeight: 700 }}>{funnel[f.key]}</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{f.label}</div>
            <div className="muted" style={{ fontSize: 11, marginTop: 4 }}>{f.hint}</div>
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>Discovery Candidates</strong>{" "}
            <span className="muted" style={{ fontSize: 12 }}>
              Pre-prospect layer — a public technical signal is not yet a buyer.
            </span>
          </div>
          <button className="ghost" onClick={reclassifyAndEnrich} disabled={running}>
            {running ? "Resolving…" : "Resolve & qualify candidates"}
          </button>
        </div>
        {candidateFunnel && (
          <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>
            {candidateFunnel.candidates} candidates · {candidateFunnel.identity_resolved} identity-resolved ·{" "}
            {candidateFunnel.verified_commercial_entities} verified commercial ·{" "}
            {candidateFunnel.commercial_unverified} commercial-unverified ·{" "}
            {candidateFunnel.not_commercial} not-commercial · {candidateFunnel.rejected} rejected ·{" "}
            {candidateFunnel.promoted_to_prospect} promoted to prospect
          </div>
        )}
        {candidates.length > 0 && (
          <div style={{ marginTop: 10 }}>
            {candidates.map((c) => (
              <div key={c.id} style={{ borderTop: "1px solid var(--border)", padding: "8px 0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 6 }}>
                  <strong>{c.canonical_name}</strong>
                  <span className="mono" style={{ fontSize: 11 }}>
                    {c.entity_type} · {c.commercial_status} · {c.activity_status}
                  </span>
                </div>
                <div className="muted" style={{ fontSize: 12, margin: "4px 0" }}>
                  <strong style={{ color: "var(--danger, #dc2626)" }}>NOT YET A PROSPECT</strong>{" "}
                  · {c.qualification_outcome || c.state}
                </div>
                <div className="muted" style={{ fontSize: 11 }}>
                  market fit {c.market_fit_confidence.toFixed(2)} · commercial{" "}
                  {c.commercial_entity_confidence.toFixed(2)} · buyer potential{" "}
                  {c.buyer_potential_confidence.toFixed(2)} · discovery priority{" "}
                  {c.discovery_priority_score.toFixed(2)}
                </div>
                {c.problem_evidence && (
                  <div className="muted" style={{ fontSize: 11, marginTop: 3 }}>
                    need: {c.need_evidence_class} — {c.problem_evidence}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {candidates.length === 0 && (
          <p className="muted" style={{ marginBottom: 0 }}>
            No discovery candidates yet. GitHub discoveries are reclassified into this
            layer rather than counted as commercial prospects.
          </p>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
        <div>
          <h3 style={{ marginTop: 4 }}>Research cohort</h3>
          {prospects.length === 0 ? (
            <div className="empty-card">
              <div className="empty-title">No prospects yet.</div>
              <p className="muted">
                Run discovery to find real organizations, or configure a campaign.
                Every prospect carries attributable evidence.
              </p>
            </div>
          ) : (
            prospects.map((p) => (
              <div className="card" key={p.id} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <div>
                    <strong>{p.company || "(unknown)"}</strong>
                    {p.industry && <span className="muted"> · {p.industry}</span>}
                    {p.location && <span className="muted"> · {p.location}</span>}
                  </div>
                  <span className="mono" style={{ fontSize: 12 }}>
                    {p.status}
                  </span>
                </div>
                <p className="muted" style={{ fontSize: 12, margin: "6px 0" }}>
                  {p.evidence || "No evidence recorded."}
                </p>
                <div style={{ display: "flex", gap: 16, fontSize: 12, flexWrap: "wrap" }}>
                  <span>
                    revenue score{" "}
                    <strong>{p.revenue_score != null ? p.revenue_score.toFixed(2) : "—"}</strong>
                  </span>
                  <span>
                    strategic{" "}
                    <strong>{p.strategic_score != null ? p.strategic_score.toFixed(2) : "—"}</strong>
                  </span>
                  <span>
                    probability{" "}
                    <strong>{p.probability != null ? Math.round(p.probability * 100) : "—"}%</strong>
                  </span>
                  {p.expected_min != null && (
                    <span>
                      range <strong>${p.expected_min.toLocaleString()}</strong>–
                      {p.expected_max != null ? `$${p.expected_max.toLocaleString()}` : "?"}
                    </span>
                  )}
                </div>
                <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>
                  identity {p.identity_confidence != null ? p.identity_confidence.toFixed(2) : "—"} · problem {p.problem_confidence != null ? p.problem_confidence.toFixed(2) : "—"} · capability {p.capability_fit_confidence != null ? p.capability_fit_confidence.toFixed(2) : "—"} · buyer {p.buyer_confidence != null ? p.buyer_confidence.toFixed(2) : "—"} · readiness {p.outreach_readiness_confidence != null ? p.outreach_readiness_confidence.toFixed(2) : "—"}
                </div>
                {p.recommended_motion && (
                  <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                    motion: {p.recommended_motion} · next: {p.recommended_next}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div>
          <h3 style={{ marginTop: 4 }}>Market theses</h3>
          {markets.length === 0 ? (
            <p className="muted">No market theses yet.</p>
          ) : (
            markets.map((m) => (
              <div className="card" key={m.id} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>{m.market}</strong>
                  <span className="mono" style={{ fontSize: 11 }}>
                    {m.status}
                  </span>
                </div>
                <p className="muted" style={{ fontSize: 12, margin: "6px 0" }}>
                  {m.buyer} · {m.commercial_model}
                </p>
                <div style={{ fontSize: 12 }}>
                  {m.expected_deal_min != null && (
                    <span>
                      deal ${m.expected_deal_min.toLocaleString()}–
                      {m.expected_deal_max != null ? `$${m.expected_deal_max.toLocaleString()}` : "?"} ·{" "}
                    </span>
                  )}
                  <span>score {m.score.toFixed(2)} · confidence {m.confidence.toFixed(2)}</span>
                </div>
              </div>
            ))
          )}

          <h3 style={{ marginTop: 14 }}>Capability Review</h3>
          <div className="card">
            <p className="muted" style={{ marginTop: 0 }}>
              Capabilities are not invented from market categories. New entries stay PROPOSED
              until the founder confirms real delivery ability or attaches proof.
            </p>
            <input placeholder="Capability name" value={capabilityName} onChange={(e) => setCapabilityName(e.target.value)} />
            <textarea placeholder="What can 11vatedTech actually deliver?" rows={3} value={capabilityDefinition} onChange={(e) => setCapabilityDefinition(e.target.value)} />
            <button className="ghost" onClick={proposeCapability} disabled={!capabilityName || !capabilityDefinition}>Propose capability</button>
            {capabilities.map((c) => (
              <div key={c.id} style={{ borderTop: "1px solid var(--border)", marginTop: 10, paddingTop: 10 }}>
                <strong>{c.name}</strong> <span className="mono">{c.status}</span>
                <div className="muted" style={{ fontSize: 12 }}>{c.definition}</div>
                {c.status === "PROPOSED" && <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
                  <button className="ghost" onClick={() => reviewCapability(c, "FOUNDER_CONFIRMED")}>Founder confirms</button>
                  <button className="ghost" onClick={() => reviewCapability(c, "RETIRED")}>Reject</button>
                </div>}
              </div>
            ))}
            {offers.length > 0 && <div className="muted" style={{ marginTop: 10 }}>Grounded offer hypotheses: {offers.length}</div>}
          </div>

          <h3 style={{ marginTop: 14 }}>Control surface</h3>
          <div className="card">
            <div style={{ fontSize: 13, display: "grid", gap: 4 }}>
              <div>
                Mode: <span className="mono">{control.mode}</span> · enabled:{" "}
                {control.enabled ? "yes" : "no"}
              </div>
              <div>
                Daily research {control.daily_research_budget} · prospect target{" "}
                {control.daily_prospect_target} · outreach cap {control.daily_outreach_cap}
              </div>
              <div>
                Min revenue score {control.min_revenue_score} · min confidence{" "}
                {control.min_evidence_confidence}
              </div>
              {control.geographies.length > 0 && (
                <div>Geographies: {control.geographies.join(", ")}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
