import { useEffect, useState } from "react";
import { api, Opportunity } from "../api";

const STAGES = [
  "discovered", "researched", "qualified", "relationship_developing",
  "outreach_ready", "contacted", "engaged", "discovery", "solution_defined",
  "proposal_ready", "proposal_sent", "negotiation", "won", "handoff",
  "delivery", "completed", "expansion", "referral", "lost", "dormant",
];

export function Opportunities() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ title: "", evidence: "", value: "" });

  const load = () =>
    api<{ opportunities: Opportunity[] }>("/opportunities")
      .then((r) => setOpportunities(r.opportunities))
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const create = async () => {
    setError("");
    try {
      const evidence = await api<{ id: string }>("/evidence", {
        method: "POST",
        body: JSON.stringify({
          source_type: "founder_entry",
          content: form.evidence,
          truth_class: "FACT",
        }),
      });
      await api("/opportunities", {
        method: "POST",
        body: JSON.stringify({
          title: form.title,
          source_evidence_id: evidence.id,
          estimated_value: form.value ? Number(form.value) : null,
        }),
      });
      setShowForm(false);
      setForm({ title: "", evidence: "", value: "" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create opportunity");
    }
  };

  const transition = async (id: string, stage: string) => {
    setError("");
    try {
      await api(`/opportunities/${id}/transition`, {
        method: "POST",
        body: JSON.stringify({ to_stage: stage }),
      });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Transition rejected");
    }
  };

  return (
    <div className="page">
      <h1>Opportunities</h1>
      <p className="muted">
        Every opportunity links to source evidence. Transitions are validated by
        the pipeline state machine.
      </p>
      {error && <div className="error">{error}</div>}

      <button className="ghost" onClick={() => setShowForm(!showForm)} style={{ margin: "10px 0 16px" }}>
        {showForm ? "Cancel" : "+ Add opportunity"}
      </button>

      {showForm && (
        <div className="card">
          <label>
            Title
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </label>
          <label>
            Source evidence (required)
            <textarea
              value={form.evidence}
              placeholder="What real evidence supports this opportunity?"
              onChange={(e) => setForm({ ...form, evidence: e.target.value })}
            />
          </label>
          <label>
            Estimated value (USD)
            <input type="number" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
          </label>
          <button className="primary" onClick={create}>Create from evidence</button>
        </div>
      )}

      {opportunities.length === 0 && !showForm ? (
        <div className="empty-card">
          <div className="empty-title">No active opportunities.</div>
          <p className="muted">
            GrowthOS will populate this only from attributable commercial
            evidence.
          </p>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr><th>Opportunity</th><th>Stage</th><th>Value</th><th>Probability</th><th>Transition</th></tr>
          </thead>
          <tbody>
            {opportunities.map((o) => (
              <tr key={o.id}>
                <td>{o.title}</td>
                <td><span className="mono">{o.stage}</span></td>
                <td className="mono">${o.estimated_value ?? "0"}</td>
                <td className="mono">{Math.round(o.probability * 100)}%</td>
                <td>
                  <select
                    defaultValue=""
                    onChange={(e) => e.target.value && transition(o.id, e.target.value)}
                    style={{ width: "auto", padding: "4px 8px" }}
                  >
                    <option value="">move…</option>
                    {STAGES.filter((s) => s !== o.stage).map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
