import { useEffect, useState } from "react";
import { api, ScoutControl } from "../api";
import { Status } from "../App";

interface Me {
  email: string;
  display_name: string;
  phone: string | null;
}

export function Settings() {
  const [me, setMe] = useState<Me | null>(null);
  const [state, setState] = useState<Record<string, number> | null>(null);
  const [scout, setScout] = useState<ScoutControl | null>(null);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    api<Me>("/auth/me").then(setMe).catch(() => {});
    api<Record<string, number>>("/health/state").then(setState).catch(() => {});
    api<{ control: ScoutControl }>("/scout/controls")
      .then((r) => setScout(r.control))
      .catch(() => {});
  }, []);

  const saveScout = async (patch: Partial<ScoutControl>) => {
    try {
      const r = await api<{ control: ScoutControl }>("/scout/controls", {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      setScout(r.control);
      setSaved("Saved.");
      setTimeout(() => setSaved(""), 2000);
    } catch (e) {
      setSaved(e instanceof Error ? e.message : "Failed to save");
    }
  };

  const logout = async () => {
    await api("/auth/logout", { method: "POST" }).catch(() => {});
    window.location.reload();
  };

  return (
    <div className="page">
      <h1>Settings</h1>

      <div className="card">
        <h3>Founder</h3>
        <div className="muted">
          {me?.display_name || "—"} · <span className="mono">{me?.email || "—"}</span>
          {me?.phone ? ` · ${me.phone}` : ""}
        </div>
        <button className="ghost" onClick={logout} style={{ marginTop: 12 }}>Sign out</button>
      </div>

      <div className="card">
        <h3>Revenue Scout</h3>
        <p className="muted">
          Autonomy mode, discovery scope, and CAN-SPAM compliance prerequisites.
          The kill switch lives on the Revenue Scout page.
        </p>
        {scout && (
          <div style={{ display: "grid", gap: 10, maxWidth: 560 }}>
            <label>
              Autonomy mode
              <select
                value={scout.mode}
                onChange={(e) => saveScout({ mode: e.target.value })}
              >
                <option value="observe">OBSERVE — research only, never outreach</option>
                <option value="assist">ASSIST — research + draft, founder approves sends</option>
                <option value="campaign_auto">CAMPAIGN_AUTO — approved campaigns send in-policy</option>
                <option value="full_research">FULL_RESEARCH — aggressive discovery, comms policy separate</option>
              </select>
            </label>
            <label>
              Daily outreach cap
              <input
                type="number"
                value={scout.daily_outreach_cap}
                onChange={(e) => saveScout({ daily_outreach_cap: Number(e.target.value) })}
              />
            </label>
            <label>
              Minimum Revenue Opportunity Score
              <input
                type="number"
                step="0.05"
                value={scout.min_revenue_score}
                onChange={(e) => saveScout({ min_revenue_score: Number(e.target.value) })}
              />
            </label>
            <label>
              Business postal address (required for outbound marketing)
              <textarea
                rows={2}
                value={scout.business_postal_address ?? ""}
                onChange={(e) =>
                  saveScout({ business_postal_address: e.target.value || null })
                }
              />
            </label>
            <label>
              Opt-out email (required for outbound marketing)
              <input
                value={scout.opt_out_email ?? ""}
                onChange={(e) =>
                  saveScout({ opt_out_email: e.target.value || null })
                }
              />
            </label>
            {saved && <div className="muted">{saved}</div>}
          </div>
        )}
      </div>

      <div className="card">
        <h3>Installation truth</h3>
        <p className="muted">Real counts from the database. Zero mock commercial data.</p>
        <table className="table">
          <thead>
            <tr><th>Entity</th><th>Count</th><th>Status</th></tr>
          </thead>
          <tbody>
            {(state
              ? Object.entries(state)
              : []
            ).map(([k, v]) => (
              <tr key={k}>
                <td className="mono">{k}</td>
                <td className="mono">{v}</td>
                <td><Status value={v === 0 ? "EMPTY" : "RECORDED"} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
