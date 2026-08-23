import { useState } from "react";
import { api } from "./api";

export function Login({ onAuthed }: { onAuthed: () => void }) {
  const [mode, setMode] = useState<"login" | "bootstrap">("login");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      if (mode === "bootstrap") {
        await api("/auth/bootstrap", {
          method: "POST",
          body: JSON.stringify({
            email,
            display_name: displayName,
            password,
          }),
        });
      } else {
        await api("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
      }
      onAuthed();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <div className="login-card">
        <div className="brand">
          <span className="brand-mark">11V</span>
          <div>
            <div className="brand-name">GrowthOS</div>
            <div className="brand-sub">11vatedTech</div>
          </div>
        </div>
        <h2>{mode === "login" ? "Founder sign in" : "First boot — create founder"}</h2>
        <p className="muted">
          Single-founder access. All commercial intelligence stays on this
          workstation.
        </p>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="founder@11vatedtech.com"
          />
        </label>
        {mode === "bootstrap" && (
          <label>
            Display name
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Founder"
            />
          </label>
        )}
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="12+ chars, upper, lower, digit"
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
        </label>

        {error && <div className="error">{error}</div>}

        <button className="primary" onClick={submit} disabled={busy}>
          {busy ? "…" : mode === "login" ? "Sign in" : "Create founder account"}
        </button>

        <button
          className="link"
          onClick={() => {
            setMode(mode === "login" ? "bootstrap" : "login");
            setError("");
          }}
        >
          {mode === "login"
            ? "First boot? Create the founder account"
            : "Already configured? Sign in"}
        </button>
      </div>
    </div>
  );
}
