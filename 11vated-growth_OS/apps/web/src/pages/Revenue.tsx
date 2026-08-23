import { useEffect, useState } from "react";
import { api, RevenueMetrics } from "../api";

export function Revenue() {
  const [metrics, setMetrics] = useState<RevenueMetrics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<RevenueMetrics>("/revenue/metrics")
      .then(setMetrics)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page">
      <h1>Revenue</h1>
      <p className="muted">Metrics derive only from persistent records. Nothing here is a hand-entered display number.</p>
      {error && <div className="error">{error}</div>}

      <div className="grid grid-2" style={{ margin: "18px 0" }}>
        <Stat label="Pipeline value" value={money(metrics?.pipeline_value)} />
        <Stat label="Weighted pipeline" value={money(metrics?.weighted_pipeline)} />
        <Stat label="Booked revenue" value={money(metrics?.booked_revenue)} />
        <Stat label="Collected revenue" value={money(metrics?.collected_revenue)} />
      </div>

      <div className="card">
        <h3>Evidence sufficiency</h3>
        {metrics && !metrics.has_sufficient_data ? (
          <p className="muted">
            Insufficient evidence exists to report sales-cycle duration, close
            rate, source attribution, or repeat business. This is reported
            honestly, not as zero-performance.
          </p>
        ) : (
          <p className="muted">
            Active opportunities: {metrics?.active_opportunities ?? 0} · Won: {metrics?.won_opportunities ?? 0}
          </p>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="card metric" style={{ marginBottom: 0 }}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

function money(value?: string): string {
  const n = Number(value ?? 0);
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}
