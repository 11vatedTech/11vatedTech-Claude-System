import { useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { api } from "./api";
import { Login } from "./auth";
import { CommandCenter } from "./pages/CommandCenter";
import { Products } from "./pages/Products";
import { Campaigns } from "./pages/Campaigns";
import { Opportunities } from "./pages/Opportunities";
import { Revenue } from "./pages/Revenue";
import { Inbox } from "./pages/Inbox";
import { AgentActivity } from "./pages/AgentActivity";
import { Settings } from "./pages/Settings";
import { Communications } from "./pages/Communications";
import { Integrations } from "./pages/Integrations";
import { GrowthAgent } from "./pages/GrowthAgent";
import { Scout } from "./pages/Scout";
import { Capabilities } from "./pages/Capabilities";

const NAV = [
  { section: "Operate", items: [
    { to: "/", label: "Command Center", exact: true },
    { to: "/inbox", label: "Founder Inbox" },
    { to: "/agent", label: "Growth Agent" },
    { to: "/scout", label: "Revenue Scout" },
  ]},
  { section: "Commercial", items: [
    { to: "/discovery", label: "Discovery" },
    { to: "/network", label: "Network" },
    { to: "/opportunities", label: "Opportunities" },
    { to: "/pipeline", label: "Pipeline" },
    { to: "/products", label: "Products" },
    { to: "/campaigns", label: "Campaigns" },
    { to: "/offers", label: "Offers" },
    { to: "/capabilities", label: "Capabilities" },
    { to: "/revenue", label: "Revenue" },
  ]},
  { section: "System", items: [
    { to: "/communications", label: "Communications" },
    { to: "/research", label: "Research" },
    { to: "/integrations", label: "Integrations" },
    { to: "/activity", label: "Agent Activity" },
    { to: "/settings", label: "Settings" },
  ]},
];

interface Me {
  display_name: string;
  email: string;
}

export function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const load = () => {
      api<Me>("/auth/me")
        .then(setMe)
        .catch(() => setMe(null))
        .finally(() => setChecking(false));
    };
    load();
    window.addEventListener("growthos:unauthorized", () => setMe(null));
    return () =>
      window.removeEventListener("growthos:unauthorized", () => setMe(null));
  }, []);

  if (checking) {
    return <div className="boot">Loading GrowthOS…</div>;
  }

  if (!me) {
    return <Login onAuthed={() => setMe({ display_name: "", email: "" })} />;
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">11V</span>
          <div>
            <div className="brand-name">GrowthOS</div>
            <div className="brand-sub">11vatedTech</div>
          </div>
        </div>
        <nav>
          {NAV.map((group) => (
            <div className="nav-group" key={group.section}>
              <div className="nav-section">{group.section}</div>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.exact}
                  className={({ isActive }) =>
                    "nav-link" + (isActive ? " active" : "")
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="dot" />
          {me.email || "founder"}
        </div>
      </aside>

      <main className="content">
        <Routes>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/agent" element={<GrowthAgent />} />
          <Route path="/scout" element={<Scout />} />
          <Route path="/discovery" element={<Placeholder title="Discovery" text="No prospects yet." />} />
          <Route path="/network" element={<Placeholder title="Network" text="No relationships yet. Import LinkedIn connections to begin." />} />
          <Route path="/opportunities" element={<Opportunities />} />
          <Route path="/pipeline" element={<Placeholder title="Pipeline" text="No active opportunities." />} />
          <Route path="/products" element={<Products />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/offers" element={<Placeholder title="Offers" text="No offers yet." />} />
          <Route path="/capabilities" element={<Capabilities />} />
          <Route path="/revenue" element={<Revenue />} />
          <Route path="/communications" element={<Communications />} />
          <Route path="/research" element={<Placeholder title="Research" text="No research runs yet." />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/activity" element={<AgentActivity />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function Placeholder({ title, text }: { title: string; text: string }) {
  return (
    <div className="page">
      <h1>{title}</h1>
      <div className="empty-card">
        <div className="empty-title">{text}</div>
        <p className="muted">
          GrowthOS populates this only from attributable commercial evidence.
        </p>
      </div>
    </div>
  );
}

export function Status({ value }: { value: string }) {
  const upper = value.toUpperCase();
  let tone = "ok";
  if (
    upper.startsWith("BLOCKED") ||
    upper.startsWith("ERROR") ||
    upper.startsWith("TOKEN") ||
    upper.startsWith("SCOPE") ||
    upper.startsWith("FAILED") ||
    upper.startsWith("DENIED")
  ) {
    tone = "danger";
  } else if (
    upper.startsWith("NOT") ||
    upper.startsWith("AUTHORIZATION") ||
    upper.startsWith("DEGRADED") ||
    upper.includes("AWAITING")
  ) {
    tone = "warn";
  }
  return <span className={"status " + tone}>{value}</span>;
}
