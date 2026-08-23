import { useEffect, useState } from "react";
import { api, CapabilityActivationState } from "../api";

interface Root { id: string; path: string; label: string | null; enabled: boolean; last_scan_at?: string | null; last_error?: string | null }
interface Proposal { id: string; name: string; definition: string; status: string; external_claimable: boolean; proof_evidence: Record<string, unknown>[]; limitations: string[]; maturity?: string | null; related_completed_work?: string[]; external_summary?: string | null; commercial_models?: { model: string; fit: string; notes: string }[] }
interface Project { id: string; name: string; path: string; git_branch: string | null; git_status: string | null; languages: string[]; manifests: string[]; source_directories: string[]; test_summary: string | null; intelligence_profile?: Record<string, unknown> }

export function Capabilities() {
  const [roots, setRoots] = useState<Root[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [rootPath, setRootPath] = useState("");
  const [tab, setTab] = useState("Overview");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [activation, setActivation] = useState<Record<string, CapabilityActivationState>>({});
  const [editing, setEditing] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDef, setEditDef] = useState("");
  const [editMaturity, setEditMaturity] = useState("PROTOTYPE_PROVEN");
  const [editLimits, setEditLimits] = useState("");
  const [editSummary, setEditSummary] = useState("");
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});

  const load = async () => {
    try {
      const [r, c, p] = await Promise.all([
        api<{ roots: Root[] }>("/scout/capability-intelligence/roots"),
        api<{ capabilities: Proposal[] }>("/scout/capabilities"),
        api<{ projects: Project[] }>("/scout/capability-intelligence/projects"),
      ]);
      setRoots(r.roots); setProposals(c.capabilities); setProjects(p.projects);
      // Load activation state for confirmed capabilities
      const confirmed = c.capabilities.filter((x) => x.status === "FOUNDER_CONFIRMED");
      const states: Record<string, CapabilityActivationState> = {};
      for (const cap of confirmed) {
        try {
          states[cap.id] = await api<CapabilityActivationState>(`/scout/capabilities/${cap.id}/activation`);
        } catch { /* activation not ready */ }
      }
      setActivation(states);
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to load Capability Intelligence"); }
  };
  useEffect(() => { load(); }, []);
  const addRoot = async () => {
    setBusy(true); setError("");
    try { await api("/scout/capability-intelligence/roots", { method: "POST", body: JSON.stringify({ path: rootPath, label: "Founder-authorized repository" }) }); setRootPath(""); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Root validation failed"); }
    finally { setBusy(false); }
  };
  const scan = async (id: string) => {
    setBusy(true); setError("");
    try { await api(`/scout/capability-intelligence/roots/${id}/inspect`, { method: "POST" }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Scan failed"); }
    finally { setBusy(false); }
  };
  const deepen = async (id: string) => {
    setBusy(true); setError("");
    try { await api(`/scout/capabilities/${id}/deepen`, { method: "POST" }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Deep evidence review failed"); }
    finally { setBusy(false); }
  };
  const confirm = async (id: string, name: string, def: string, maturity: string, limitations: string[], summary: string) => {
    try {
      await api(`/scout/capabilities/${id}/confirm`, {
        method: "POST",
        body: JSON.stringify({ name, definition: def, maturity, limitations, external_summary: summary, note: "Founder Edit & Confirm from Capability Intelligence" }),
      });
      setEditing(null); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Confirm failed"); }
  };
  const reject = async (id: string) => {
    try {
      await api(`/scout/capabilities/${id}/reject`, { method: "POST", body: JSON.stringify({ reason: rejectReason[id] || "Rejected by founder for this evidence chain" }) });
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Reject failed"); }
  };
  const activate = async (id: string) => {
    setBusy(true); setError("");
    try { await api(`/scout/capabilities/${id}/activate`, { method: "POST" }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Activation failed"); }
    finally { setBusy(false); }
  };
  const discover = async (id: string) => {
    setBusy(true); setError("");
    try { await api(`/scout/capabilities/${id}/discover?limit=15`, { method: "POST" }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Discovery failed"); }
    finally { setBusy(false); }
  };
  const tabs = ["Overview", "Proposed", "Confirmed", "Verified", "Restricted", "Rejected", "Gaps", "Project Evidence", "Evidence Sources"];
  const visible = tab === "Proposed" ? proposals.filter(p => p.status === "PROPOSED") : tab === "Confirmed" ? proposals.filter(p => p.status === "FOUNDER_CONFIRMED") : tab === "Verified" ? proposals.filter(p => p.status === "EVIDENCE_VERIFIED") : tab === "Restricted" ? proposals.filter(p => p.status === "RESTRICTED") : tab === "Rejected" ? proposals.filter(p => p.status === "REJECTED") : proposals;
  const counts = {
    proposed: proposals.filter(p => p.status === "PROPOSED").length,
    confirmed: proposals.filter(p => p.status === "FOUNDER_CONFIRMED").length,
    rejected: proposals.filter(p => p.status === "REJECTED").length,
  };
  return <div className="page">
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline"}}><div><h1 style={{marginBottom:0}}>Capabilities</h1><p className="muted">What 11vatedTech can demonstrably deliver — grounded in private project evidence and founder review.</p></div><span className="status warn">Outbound disabled</span></div>
    {error && <div className="error">{error}</div>}
    <div className="tabs" style={{display:"flex",gap:6,flexWrap:"wrap",margin:"18px 0"}}>{tabs.map(t => <button key={t} className={tab === t ? "primary" : "ghost"} onClick={() => setTab(t)}>{t}</button>)}</div>
    {tab === "Evidence Sources" && <section className="card"><h3>Evidence Sources</h3><p className="muted">Only explicitly authorized paths are scanned. GrowthOS never crawls parent directories.</p><div style={{display:"flex",gap:8}}><input style={{flex:1}} placeholder="Founder-authorized repository path" value={rootPath} onChange={e => setRootPath(e.target.value)} /><button className="primary" disabled={!rootPath || busy} onClick={addRoot}>ADD ROOT</button></div>{roots.map(r => <div className="card" key={r.id} style={{marginTop:10}}><strong>{r.label || "Repository root"}</strong><div className="mono" style={{fontSize:12,marginTop:5}}>{r.path}</div><div className="muted" style={{fontSize:12,marginTop:5}}>Authorization: founder-authorized · Enabled: {r.enabled ? "yes" : "no"} · Last scan: {r.last_scan_at ? new Date(r.last_scan_at).toLocaleString() : "never"}</div><button className="ghost" style={{marginTop:8}} disabled={busy} onClick={() => scan(r.id)}>SCAN / RESCAN</button></div>)}</section>}
    {tab === "Project Evidence" && <section><h3>Projects / Evidence</h3>{projects.length === 0 ? <div className="empty-card"><div className="empty-title">No trusted project has been scanned yet.</div><p className="muted">Add the explicitly authorized repository under Evidence Sources.</p></div> : projects.map(p => <div className="card" key={p.id} style={{marginBottom:10}}><div style={{display:"flex",justifyContent:"space-between"}}><strong>{p.name}</strong><span className="mono">{p.git_branch || "branch unknown"}</span></div><div className="muted" style={{fontSize:12,marginTop:6}}>Git: {p.git_status || "unknown"} · Languages: {p.languages.join(", ") || "unknown"}</div><div style={{fontSize:12,marginTop:6}}>Manifests: {p.manifests.slice(0,6).join(", ") || "none detected"}</div><div className="muted" style={{fontSize:12,marginTop:6}}>Tests: {p.test_summary || "not detected"}</div></div>)}</section>}
    {tab !== "Evidence Sources" && tab !== "Project Evidence" && <section><div className="grid grid-3" style={{marginBottom:16}}><div className="card"><div className="muted">Proposed</div><strong style={{fontSize:24}}>{counts.proposed}</strong></div><div className="card"><div className="muted">Founder confirmed</div><strong style={{fontSize:24}}>{counts.confirmed}</strong></div><div className="card"><div className="muted">Rejected (evidence chain)</div><strong style={{fontSize:24}}>{counts.rejected}</strong></div></div>{tab === "Overview" && <div className="card" style={{marginBottom:14}}><strong>Review boundary</strong><p className="muted" style={{marginBottom:0}}>Proposals are generated from actual repositories but remain non-marketable until the founder confirms them. Confirmation triggers selective prospect requalification and offer/market hypotheses; it will not send outreach. A rejection only rejects the evidence chain, never the whole company capability.</p></div>}{tab === "Gaps" ? <div className="empty-card"><div className="empty-title">Capability gaps</div><p className="muted">No capability gaps have been generated yet.</p></div> : visible.map(p => <div className="card" key={p.id} style={{marginBottom:10}}>
      {editing === p.id ? (
        <div>
          <h3 style={{margin:"0 0 5px"}}>Edit & Confirm — {p.name}</h3>
          <div style={{display:"flex",flexDirection:"column",gap:8,marginTop:10}}>
            <label className="muted" style={{fontSize:12}}>Canonical name</label>
            <input value={editName} onChange={e => setEditName(e.target.value)} />
            <label className="muted" style={{fontSize:12}}>Commercial definition</label>
            <textarea rows={4} value={editDef} onChange={e => setEditDef(e.target.value)} />
            <label className="muted" style={{fontSize:12}}>External summary (customer-facing, sanitized)</label>
            <textarea rows={3} value={editSummary} onChange={e => setEditSummary(e.target.value)} />
            <label className="muted" style={{fontSize:12}}>Limitations (one per line)</label>
            <textarea rows={5} value={editLimits} onChange={e => setEditLimits(e.target.value)} />
            <label className="muted" style={{fontSize:12}}>Delivery maturity</label>
            <select value={editMaturity} onChange={e => setEditMaturity(e.target.value)}>
              {["EXPERIMENTAL","PROTOTYPE_PROVEN","INTERNAL_PROVEN","CLIENT_READY","PRODUCTION_PROVEN"].map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <div style={{display:"flex",gap:8}}>
              <button className="primary" onClick={() => confirm(p.id, editName, editDef, editMaturity, editLimits.split("\n").map(x=>x.trim()).filter(Boolean), editSummary)}>CONFIRM</button>
              <button className="ghost" onClick={() => setEditing(null)}>CANCEL</button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div style={{display:"flex",justifyContent:"space-between",gap:10}}><div><h3 style={{margin:"0 0 5px"}}>{p.name}</h3><div className="muted">{p.definition}</div></div><span className="mono">{p.status}</span></div>
          <div style={{marginTop:12,fontSize:13}}><strong>What proves it?</strong><ul>{p.proof_evidence.map((e,i) => <li key={i}>{String(e.reason || e.summary || "Evidence recorded")} {e.project ? ` · ${String(e.project)}` : ""}</li>)}</ul></div>
          <div style={{fontSize:13}}><strong>Known limitations</strong><div className="muted">{p.limitations.length ? p.limitations.join(" · ") : "Founder review required; no external limitations asserted yet."}</div></div>
          {p.status === "PROPOSED" && <div style={{display:"flex",gap:8,marginTop:12,flexWrap:"wrap"}}>
            <button className="primary" onClick={() => { setEditing(p.id); setEditName(p.name); setEditDef(p.definition); setEditMaturity(p.maturity || "PROTOTYPE_PROVEN"); setEditLimits(p.limitations.join("\n")); setEditSummary(p.external_summary || ""); }}>EDIT & CONFIRM</button>
            <button className="ghost" onClick={() => deepen(p.id)} disabled={busy}>REQUEST MORE EVIDENCE</button>
            <button className="ghost" onClick={() => { setEditing(p.id); setEditName(p.name); setEditDef(p.definition); setEditMaturity(p.maturity || "PROTOTYPE_PROVEN"); setEditLimits(p.limitations.join("\n")); setEditSummary(p.external_summary || ""); }}>CONFIRM</button>
            <button className="ghost" onClick={() => { setRejectReason(prev => ({ ...prev, [p.id]: "Rejected by founder for this evidence chain" })); reject(p.id); }}>REJECT</button>
            <button className="ghost" onClick={() => { setRejectReason(prev => ({ ...prev, [p.id]: "" })); }}>REJECT (custom)</button>
            {rejectReason[p.id] !== undefined && rejectReason[p.id] === "" && <div style={{display:"flex",gap:6,alignItems:"center",width:"100%"}}><input placeholder="Rejection reason" value={rejectReason[p.id]} onChange={e => setRejectReason(prev => ({ ...prev, [p.id]: e.target.value }))} /><button className="danger" onClick={() => reject(p.id)}>CONFIRM REJECT</button></div>}
          </div>}
          {p.status === "FOUNDER_CONFIRMED" && <div style={{display:"flex",gap:8,marginTop:12,flexWrap:"wrap"}}>
            <button className="primary" onClick={() => activate(p.id)} disabled={busy}>RUN ACTIVATION PIPELINE</button>
            <button className="ghost" onClick={() => discover(p.id)} disabled={busy}>RUN DISCOVERY EXPERIMENT</button>
          </div>}
          {p.status === "FOUNDER_CONFIRMED" && activation[p.id] && <ActivationDetail state={activation[p.id]} />}
        </div>
      )}
    </div>)}</section>}
  </div>;
}

function ActivationDetail({ state }: { state: CapabilityActivationState }) {
  return <div style={{marginTop:14,borderTop:"1px solid var(--border, #333)",paddingTop:12}}>
    <div className="muted" style={{fontSize:12,marginBottom:8}}>Activation state · Outbound {state.outbound}</div>
    {state.capability.external_summary && <div className="card" style={{marginBottom:8}}><strong>External summary (customer-facing)</strong><p className="muted" style={{marginBottom:0}}>{state.capability.external_summary}</p></div>}
    <div className="grid grid-2" style={{marginBottom:8}}>
      <div className="card"><strong>Commercial models</strong><ul style={{fontSize:12,margin:"6px 0 0"}}>{state.capability.commercial_models.map((m,i) => <li key={i}><b>{m.model}</b> — <span className={"status " + (m.fit === "FIT" ? "ok" : m.fit === "NOT_CURRENTLY_SUPPORTED" ? "danger" : "warn")}>{m.fit}</span><div className="muted">{m.notes}</div></li>)}</ul></div>
      <div className="card"><strong>Offer hypotheses</strong><ul style={{fontSize:12,margin:"6px 0 0"}}>{state.offers.map(o => <li key={o.id}><b>{o.name}</b> <span className="mono">{o.status}</span><div className="muted">{o.buyer} · {o.timeline_hypothesis}</div></li>)}</ul></div>
    </div>
    <div className="card" style={{marginBottom:8}}><strong>Capability-driven market theses</strong><p className="muted" style={{fontSize:12,margin:"4px 0 8px"}}>Generated autonomously from the confirmed capability; all are hypotheses.</p>
      <table style={{width:"100%",fontSize:12}}><thead><tr><th style={{textAlign:"left"}}>Market</th><th>Score</th><th>Short</th><th>Strategic</th><th>Conf</th></tr></thead><tbody>{state.market_theses.map(t => <tr key={t.id}><td>{t.market}</td><td style={{textAlign:"center"}}>{t.score.toFixed(2)}</td><td style={{textAlign:"center"}}>{t.short_term_score.toFixed(2)}</td><td style={{textAlign:"center"}}>{t.strategic_score.toFixed(2)}</td><td style={{textAlign:"center"}}>{t.confidence.toFixed(2)}</td></tr>)}</tbody></table>
      {state.market_theses[0] && <div className="muted" style={{fontSize:12,marginTop:8}}>Selected validation market: <b>{state.market_theses[0].market}</b> — {state.market_theses[0].selection_reasoning}</div>}
    </div>
    <div className="grid grid-2">
      <div className="card"><strong>Problem ↔ capability graph</strong><ul style={{fontSize:12,margin:"6px 0 0"}}>{state.problem_canon.map(p => <li key={p.id}>{p.name} <span className="mono">{p.status}</span></li>)}</ul></div>
      <div className="card"><strong>Product / IP potential</strong><ul style={{fontSize:12,margin:"6px 0 0"}}>{state.product_hypotheses.map(h => <li key={h.id}><b>{h.hypothesis_type}</b> — {h.name}<div className="muted">{h.rationale}</div></li>)}</ul></div>
    </div>
  </div>;
}
