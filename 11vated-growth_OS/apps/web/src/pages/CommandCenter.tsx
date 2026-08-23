import { useEffect, useState } from "react";
import { api, HealthState, RevenueMetrics } from "../api";

export function CommandCenter() {
  const [state, setState] = useState<HealthState | null>(null);
  const [revenue, setRevenue] = useState<RevenueMetrics | null>(null);
  const [needsResponse, setNeedsResponse] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    api<HealthState>("/health/state")
      .then(setState)
      .catch((e) => setError(e.message));
    api<RevenueMetrics>("/revenue/metrics").then(setRevenue).catch(() => {});
    api<{ items: { status: string }[] }>("/inbox")
      .then((r) =>
        setNeedsResponse(r.items.filter((i) => i.status === "unread").length),
      )
      .catch(() => {});
  }, []);

  return (
    <div className="page">
      <h1>Command Center</h1>
      <p className="muted">What deserves your attention right now.</p>

      {error && <div className="error">{error}</div>}

      <div className="grid grid-4" style={{ margin: "18px 0" }}>
        <Metric label="Prospects" value={state?.prospects} />
        <Metric label="Opportunities" value={state?.opportunities} />
        <Metric label="Campaigns" value={state?.campaigns} />
        <Metric label="Products" value={state?.products} />
      </div>

      {needsResponse > 0 && (
        <div className="card" style={{ borderLeft: "3px solid var(--accent)" }}>
          <div style={{ fontWeight: 600 }}>
            {needsResponse} item{needsResponse === 1 ? "" : "s"} need{" "}
            your response in the Founder Inbox.
          </div>
          <p className="muted">Derived from real FounderInboxItems only.</p>
        </div>
      )}

      <div className="card">
        <h3>Revenue truth</h3>
        <div className="grid grid-2">
          <Metric
            label="Pipeline value"
            value={money(revenue?.pipeline_value)}
            sub={`Weighted: ${money(revenue?.weighted_pipeline)}`}
          />
          <Metric
            label="Collected revenue"
            value={money(revenue?.collected_revenue)}
            sub={`Booked: ${money(revenue?.booked_revenue)}`}
          />
        </div>
        {revenue && !revenue.has_sufficient_data && (
          <p className="muted" style={{ marginTop: 12 }}>
            Insufficient evidence to report commercial performance. This is
            correct behavior on a fresh installation.
          </p>
        )}
      </div>

      <div className="card">
        <h3>Start</h3>
        <div className="grid grid-2">
          <StartAction title="Market a Product" to="/products" />
          <StartAction title="Review the Founder Inbox" to="/inbox" />
          <StartAction title="Add an Opportunity" to="/opportunities" />
          <StartAction title="Configure Integrations" to="/integrations" />
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, sub }: { label: string; value?: string | number; sub?: string }) {
  return (
    <div className="card metric" style={{ marginBottom: 0 }}>
      <div className="label">{label}</div>
      <div className="value">{value ?? 0}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}

function StartAction({ title, to }: { title: string; to: string }) {
  return (
    <a className="nav-link" href={to} style={{ border: "1px solid var(--border)", padding: "12px" }}>
      {title} →
    </a>
  );
}

function money(value?: string): string {
  if (value === undefined || value === null) return "$0";
  const n = Number(value);
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}
