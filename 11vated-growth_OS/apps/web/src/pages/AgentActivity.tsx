import { useEffect, useState } from "react";
import { api, Job } from "../api";

export function AgentActivity() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ jobs: Job[] }>("/jobs")
      .then((r) => setJobs(r.jobs))
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page">
      <h1>Agent Activity</h1>
      <p className="muted">Persistent job history with retry, backoff, idempotency, and dead-letter state.</p>
      {error && <div className="error">{error}</div>}

      {jobs.length === 0 ? (
        <div className="empty-card">
          <div className="empty-title">No agent activity yet.</div>
          <p className="muted">Nothing consequential has happened invisibly.</p>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr><th>Type</th><th>State</th><th>Attempts</th><th>Error</th></tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td className="mono">{j.type}</td>
                <td><span className="mono">{j.state}</span></td>
                <td className="mono">{j.attempts}/{j.max_attempts}</td>
                <td className="muted" style={{ maxWidth: 400, overflow: "hidden", textOverflow: "ellipsis" }}>
                  {j.error ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
