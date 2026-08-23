import { useEffect, useState } from "react";
import { api } from "../api";
import { Status } from "../App";

interface IntegrationRow {
  provider: string;
  state: string;
  configured: boolean;
  account?: string | null;
  last_checked_at?: string | null;
  last_sync_at?: string | null;
  messages_ingested?: number;
  error_message?: string | null;
  publishing_state_note?: string;
  model_available?: boolean;
  model_pull_state?: string;
  generation_ok?: boolean;
  structured_output_ok?: boolean;
  tool_selection_ok?: boolean;
  latency_ms?: number;
  models_installed?: string[];
}

export function Integrations() {
  const [rows, setRows] = useState<IntegrationRow[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () =>
    api<{ integrations: IntegrationRow[] }>("/integrations")
      .then((r) => setRows(r.integrations))
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const syncNow = async () => {
    setBusy(true);
    try {
      const r = await api<{ job_id: string; status: string }>("/integrations/gmail/sync", {
        method: "POST",
      });
      setError(`Sync scheduled (job ${r.job_id}).`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async () => {
    if (!window.confirm("Disconnect Gmail? Tokens will be revoked and removed.")) return;
    try {
      await api("/integrations/gmail/disconnect", { method: "POST" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Disconnect failed");
    }
  };

  return (
    <div className="page">
      <h1>Integrations</h1>
      <p className="muted">
        Real connection state only — no simulated healthy status.
      </p>
      {error && <div className="error">{error}</div>}

      {rows.map((row) => (
        <div className="card" key={row.provider} style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontWeight: 600, textTransform: "capitalize" }}>
                {row.provider.replace("_", " ")}
              </div>
              {row.account && <div className="muted">{row.account}</div>}
              <div style={{ marginTop: 4 }}>
                <Status value={row.state} />
              </div>
              {row.last_sync_at && (
                <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                  Last sync: {new Date(row.last_sync_at).toLocaleString()} ·{" "}
                  {row.messages_ingested ?? 0} messages ingested
                </div>
              )}
              {row.error_message && (
                <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                  Error: {row.error_message}
                </div>
              )}
            </div>
            {row.provider === "gmail" && (
              <div style={{ display: "flex", gap: 6 }}>
                <button className="ghost" onClick={syncNow} disabled={busy}>
                  {busy ? "…" : "Sync now"}
                </button>
                <button className="ghost" onClick={disconnect}>
                  Disconnect
                </button>
              </div>
            )}
          </div>
          {row.provider === "gmail" && row.publishing_state_note && (
            <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
              {row.publishing_state_note}
            </div>
          )}
          {row.provider === "ollama" && (
            <div style={{ fontSize: 13, marginTop: 10, lineHeight: 1.7 }}>
              <div>
                Model: <strong>{row.account ?? "—"}</strong> ·{" "}
                {row.model_available ? (
                  <span className="status ok">MODEL AVAILABLE</span>
                ) : (
                  <span className="status warn">MODEL MISSING</span>
                )}
              </div>
              <div className="muted">
                generation {row.generation_ok ? "✓" : "✗"} · structured
                output {row.structured_output_ok ? "✓" : "✗"} · tool
                selection {row.tool_selection_ok ? "✓" : "✗"}
                {row.latency_ms ? ` · ${row.latency_ms}ms` : ""}
              </div>
              {row.models_installed && row.models_installed.length > 0 && (
                <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                  Installed: {row.models_installed.join(", ")}
                </div>
              )}
              {!row.model_available && (
                <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                  Run <code>ollama pull {row.account}</code> to install the
                  configured model. No cloud fallback is used.
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
