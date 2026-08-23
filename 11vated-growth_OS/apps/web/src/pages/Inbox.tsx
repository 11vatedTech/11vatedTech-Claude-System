import { useEffect, useState } from "react";
import { api, InboxItem } from "../api";

export function Inbox() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [error, setError] = useState("");

  const load = () =>
    api<{ items: InboxItem[] }>("/inbox")
      .then((r) => setItems(r.items))
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const action = async (id: string, a: string) => {
    await api(`/inbox/${id}/action`, {
      method: "POST",
      body: JSON.stringify({ action: a }),
    });
    load();
  };

  return (
    <div className="page">
      <h1>Founder Inbox</h1>
      <p className="muted">Generated entirely from real events. No manual fake insertion.</p>
      {error && <div className="error">{error}</div>}

      {items.length === 0 ? (
        <div className="empty-card">
          <div className="empty-title">Inbox is empty.</div>
          <p className="muted">Nothing needs you right now.</p>
        </div>
      ) : (
        <div>
          {items.map((i) => (
            <div className="card" key={i.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 600 }}>{i.title}</div>
                <div className="muted">{i.summary || i.kind}</div>
                <div className="muted mono" style={{ fontSize: 11 }}>{i.kind} · {i.status}</div>
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                <button className="ghost" onClick={() => action(i.id, "actioned")}>Done</button>
                <button className="ghost" onClick={() => action(i.id, "dismissed")}>Dismiss</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
