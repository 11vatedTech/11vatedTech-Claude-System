import { useEffect, useState } from "react";
import { api, Campaign, Product } from "../api";

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", product_id: "", objective: "" });

  const load = () => {
    api<{ campaigns: Campaign[] }>("/campaigns")
      .then((r) => setCampaigns(r.campaigns))
      .catch((e) => setError(e.message));
    api<{ products: Product[] }>("/products")
      .then((r) => setProducts(r.products))
      .catch(() => {});
  };

  useEffect(load, []);

  const create = async () => {
    setError("");
    try {
      await api("/campaigns", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setShowForm(false);
      setForm({ name: "", product_id: "", objective: "" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create campaign");
    }
  };

  return (
    <div className="page">
      <h1>Campaigns</h1>
      <p className="muted">Market a product → a persisted Campaign. New campaigns start with 0 real prospects.</p>
      {error && <div className="error">{error}</div>}

      <button className="ghost" onClick={() => setShowForm(!showForm)} style={{ margin: "10px 0 16px" }}>
        {showForm ? "Cancel" : "+ New campaign"}
      </button>

      {showForm && (
        <div className="card">
          <label>
            Campaign name
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Product
            <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
              <option value="">Select a product…</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>
          <label>
            Objective
            <input value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} />
          </label>
          <button className="primary" onClick={create}>Create campaign</button>
        </div>
      )}

      {campaigns.length === 0 && !showForm ? (
        <div className="empty-card">
          <div className="empty-title">No campaigns yet.</div>
          <p className="muted">Create one from a Product to begin market development.</p>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr><th>Campaign</th><th>Objective</th><th>Status</th><th>Prospects</th></tr>
          </thead>
          <tbody>
            {campaigns.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td className="muted">{c.objective || "—"}</td>
                <td><span className="mono">{c.status}</span></td>
                <td className="mono">0 real prospects</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
