import { useEffect, useState } from "react";
import { api, Product, ProductIntelligence, ProductVersion } from "../api";

export function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selected, setSelected] = useState<Product | null>(null);
  const [intel, setIntel] = useState<ProductIntelligence | null>(null);
  const [versions, setVersions] = useState<ProductVersion[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", description: "", features: "" });

  const load = () =>
    api<{ products: Product[] }>("/products")
      .then((r) => setProducts(r.products))
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const openDetail = (p: Product) => {
    setSelected(p);
    setIntel(null);
    setVersions([]);
    setError("");
    api<ProductIntelligence>(`/agent/products/${p.id}/intelligence`)
      .then(setIntel)
      .catch((e) => setError(e.message));
    api<{ versions: ProductVersion[] }>(`/products/${p.id}/versions`)
      .then((r) => setVersions(r.versions))
      .catch(() => {});
  };

  const create = async () => {
    setError("");
    try {
      await api("/products", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          description: form.description,
          features: form.features
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      });
      setShowForm(false);
      setForm({ name: "", description: "", features: "" });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create product");
    }
  };

  if (selected) {
    return (
      <ProductDetail
        product={selected}
        intel={intel}
        versions={versions}
        onBack={() => {
          setSelected(null);
          load();
        }}
      />
    );
  }

  return (
    <div className="page">
      <h1>Products</h1>
      <p className="muted">The Product Canon — persistent, versioned, truth-tagged.</p>
      {error && <div className="error">{error}</div>}

      <button className="ghost" onClick={() => setShowForm(!showForm)} style={{ margin: "10px 0 16px" }}>
        {showForm ? "Cancel" : "+ Add product"}
      </button>

      {showForm && (
        <div className="card">
          <label>
            Name
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Description
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </label>
          <label>
            Features (one per line)
            <textarea value={form.features} onChange={(e) => setForm({ ...form, features: e.target.value })} />
          </label>
          <button className="primary" onClick={create}>Create product</button>
        </div>
      )}

      {products.length === 0 && !showForm ? (
        <div className="empty-card">
          <div className="empty-title">No products yet.</div>
          <p className="muted">
            Open the <strong>Growth Agent</strong> and describe what you built —
            GrowthOS will extract the Product Canon. Or add a product here to seed it.
          </p>
        </div>
      ) : (
        <div className="grid grid-2">
          {products.map((p) => (
            <div className="card" key={p.id} style={{ cursor: "pointer" }} onClick={() => openDetail(p)}>
              <h3>{p.name}</h3>
              {p.codename && <div className="muted">codename: {p.codename}</div>}
              <p className="muted">{p.description || p.definition || "No description."}</p>
              <div className="muted" style={{ fontSize: 12 }}>
                maturity: <span className="mono">{p.maturity ?? "idea"}</span>
              </div>
              {p.features.length > 0 && (
                <ul style={{ paddingLeft: 18, color: "var(--text-dim)" }}>
                  {p.features.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              )}
              <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                → open detail
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      {children}
    </div>
  );
}

function Bullets({ items, empty = "—" }: { items: unknown[]; empty?: string }) {
  if (!items || items.length === 0) return <span className="muted">{empty}</span>;
  return (
    <ul style={{ paddingLeft: 18, color: "var(--text-dim)", margin: 0 }}>
      {items.map((s, i) => (
        <li key={i}>{typeof s === "string" ? s : JSON.stringify(s)}</li>
      ))}
    </ul>
  );
}

function ProductDetail({
  product,
  intel,
  versions,
  onBack,
}: {
  product: Product;
  intel: ProductIntelligence | null;
  versions: ProductVersion[];
  onBack: () => void;
}) {
  const canon: NonNullable<Product["canon"]> =
    product.canon ?? ({} as NonNullable<Product["canon"]>);
  const readiness = intel?.sales_readiness;
  const pricing = intel?.pricing;
  const market = intel?.market_map;
  const models = intel?.commercial_models;

  const scoreBar = (score: number) => (
    <div style={{ background: "#1a1a1a", borderRadius: 6, height: 8, marginTop: 4 }}>
      <div
        style={{
          width: `${Math.max(0, Math.min(100, score))}%`,
          background: score >= 60 ? "#16a34a" : score >= 30 ? "#d97706" : "#dc2626",
          height: 8,
          borderRadius: 6,
        }}
      />
    </div>
  );

  return (
    <div className="page">
      <button className="ghost" onClick={onBack} style={{ marginBottom: 12 }}>← All products</button>
      <h1>{product.name}</h1>
      {product.codename && <p className="muted">codename: {product.codename}</p>}
      <p className="muted">
        maturity: <span className="mono">{product.maturity ?? "idea"}</span> · status: {product.status}
      </p>

      {/* Overview */}
      <Section title="Overview">
        {product.definition && <p><strong>Definition:</strong> {product.definition}</p>}
        {product.core_problem && <p><strong>Core problem:</strong> {product.core_problem}</p>}
        {product.core_insight && <p><strong>Core insight:</strong> {product.core_insight}</p>}
        {product.positioning && <p><strong>Positioning:</strong> {product.positioning}</p>}
        {!product.definition && !product.core_problem && <span className="muted">Unknown stays unknown until the founder provides it.</span>}
      </Section>

      {/* Canon */}
      <Section title="Canon">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Features</div>
            <Bullets items={canon.features ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Capabilities</div>
            <Bullets items={canon.capabilities ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Value propositions</div>
            <Bullets items={canon.value_propositions ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Target customers</div>
            <Bullets items={canon.target_customers ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Buyers</div>
            <Bullets items={canon.buyers ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Industries</div>
            <Bullets items={canon.industries ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Limitations</div>
            <Bullets items={canon.limitations ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Risks</div>
            <Bullets items={canon.risks ?? []} />
          </div>
        </div>
        {(canon.claims ?? []).length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div className="muted" style={{ fontSize: 12 }}>Truth-tagged claims</div>
            <ul style={{ paddingLeft: 18, color: "var(--text-dim)", margin: 0 }}>
              {(canon.claims as Record<string, unknown>[]).map((c, i) => (
                <li key={i}>
                  {String(c.text ?? "").slice(0, 140)}
                  {c.tag ? <span className="mono" style={{ opacity: 0.6 }}> [{String(c.tag)}]</span> : null}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Section>

      {/* Market Map */}
      <Section title="Market Map">
        <p>
          <strong>Primary market hypothesis:</strong>{" "}
          {market?.primary_market_hypothesis || <span className="muted">unknown</span>}
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Secondary markets</div>
            <Bullets items={market?.secondary_markets ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Emerging applications</div>
            <Bullets items={market?.emerging_applications ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>ICP hypotheses</div>
            <Bullets items={market?.ideal_customer_profiles ?? []} />
          </div>
          <div>
            <div className="muted" style={{ fontSize: 12 }}>Buyer roles</div>
            <Bullets items={market?.buyer_roles ?? []} />
          </div>
        </div>
        <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>
          {market?.evidence_gap_note ?? "All market conclusions are HYPOTHESIS until validated by real evidence."}
        </p>
      </Section>

      {/* Sales Readiness */}
      <Section title="Sales Readiness">
        {readiness ? (
          <>
            <p>
              Overall: <strong>{readiness.overall}/100</strong>
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {Object.entries(readiness.components).map(([name, c]) => (
                <div key={name}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                    <span className="mono" style={{ textTransform: "capitalize" }}>{name.replace(/_/g, " ")}</span>
                    <span>{c.score}/100</span>
                  </div>
                  {scoreBar(c.score)}
                  <div className="muted" style={{ fontSize: 11, marginTop: 2 }}>{c.reasoning}</div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <span className="muted">Loading…</span>
        )}
      </Section>

      {/* Pricing */}
      <Section title="Pricing">
        {pricing?.hypotheses?.length ? (
          <ul style={{ paddingLeft: 18, color: "var(--text-dim)", margin: 0 }}>
            {pricing.hypotheses.map((h, i) => (
              <li key={i}>
                <span className="mono">{h.label ?? "PRICING HYPOTHESIS"}</span>
                {" — "}
                {h.target_price != null ? `$${h.target_price}` : "no target price yet"}
                {h.range ? ` (range $${h.range[0]}–$${h.range[1]})` : ""}
                {h.confidence != null ? ` · confidence ${h.confidence}` : ""}
                {h.reasoning ? <div className="muted" style={{ fontSize: 12 }}>{h.reasoning}</div> : null}
              </li>
            ))}
          </ul>
        ) : (
          <span className="muted">No pricing hypothesis yet — pricing stays hypothesis until real sales evidence.</span>
        )}
        <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>
          Final externally communicated price requires founder approval.
        </p>
      </Section>

      {/* Commercial models */}
      <Section title="Commercial Model Analysis">
        {models ? (
          <ul style={{ paddingLeft: 18, color: "var(--text-dim)", margin: 0 }}>
            {models.analysis.map((a, i) => (
              <li key={i}>
                <span className="mono" style={{ textTransform: "capitalize" }}>{a.model.replace(/_/g, " ")}</span>
                {" — "}{a.fit}
              </li>
            ))}
          </ul>
        ) : (
          <span className="muted">Loading…</span>
        )}
      </Section>

      {/* Versions */}
      <Section title="Versions">
        {versions.length ? (
          <ul style={{ paddingLeft: 18, color: "var(--text-dim)", margin: 0 }}>
            {versions.map((v) => (
              <li key={v.version}>
                v{v.version} — {v.change_summary}{" "}
                <span className="muted" style={{ fontSize: 12 }}>
                  ({v.created_by}, {new Date(v.created_at).toLocaleString()})
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <span className="muted">No versions recorded yet.</span>
        )}
      </Section>
    </div>
  );
}
