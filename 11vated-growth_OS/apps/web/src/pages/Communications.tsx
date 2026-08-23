import { useEffect, useState } from "react";
import { api } from "../api";

interface MessageRow {
  id: string;
  direction: string;
  sender_ref?: string | null;
  subject?: string | null;
  body?: string | null;
  timestamp: string;
  attachments?: { filename: string }[];
}

interface ConversationRow {
  id: string;
  channel: string;
  title?: string | null;
  external_thread_id?: string | null;
  last_message_at?: string | null;
  status: string;
  messages: MessageRow[];
}

export function Communications() {
  const [rows, setRows] = useState<ConversationRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ conversations: ConversationRow[] }>("/communications")
      .then((r) => setRows(r.conversations))
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page">
      <h1>Communications</h1>
      <p className="muted">Real conversations only. No simulated cards.</p>
      {error && <div className="error">{error}</div>}

      {rows.length === 0 ? (
        <div className="empty-card">
          <div className="empty-title">No conversations yet.</div>
          <p className="muted">GrowthOS populates this only from real messages.</p>
        </div>
      ) : (
        rows.map((c) => (
          <div className="card" key={c.id} style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 600 }}>{c.title || "(no subject)"}</div>
            <div className="muted" style={{ fontSize: 12 }}>
              {c.channel} · {c.messages.length} messages
              {c.last_message_at
                ? ` · last ${new Date(c.last_message_at).toLocaleString()}`
                : ""}
            </div>
            {c.messages.map((m) => (
              <div
                key={m.id}
                style={{
                  marginTop: 8,
                  padding: 8,
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                }}
              >
                <div className="muted" style={{ fontSize: 12 }}>
                  {m.direction} · {m.sender_ref || "unknown"} ·{" "}
                  {new Date(m.timestamp).toLocaleString()}
                  {m.attachments && m.attachments.length > 0
                    ? ` · ${m.attachments.length} attachment(s)`
                    : ""}
                </div>
                <div style={{ marginTop: 4, whiteSpace: "pre-wrap" }}>{m.body}</div>
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  );
}
