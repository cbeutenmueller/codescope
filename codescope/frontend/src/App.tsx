import { Routes, Route, NavLink, useSearchParams } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Findings from "./pages/Findings";
import Hotspots from "./pages/Hotspots";
import Patterns from "./pages/Patterns";

const nav: Record<string, string> = {
  "/": "Dashboard",
  "/findings": "Findings",
  "/hotspots": "Hotspots",
  "/patterns": "Patterns",
};

const css = {
  shell: {
    display: "grid",
    gridTemplateRows: "48px 1fr",
    gridTemplateColumns: "180px 1fr",
    minHeight: "100vh",
  } as React.CSSProperties,
  header: {
    gridColumn: "1 / -1",
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "0 20px",
    background: "#161b22",
    borderBottom: "1px solid #30363d",
    fontSize: 14,
    fontWeight: 700,
    letterSpacing: 0.5,
  } as React.CSSProperties,
  sidebar: {
    background: "#161b22",
    borderRight: "1px solid #30363d",
    padding: "16px 0",
    display: "flex",
    flexDirection: "column",
    gap: 2,
  } as React.CSSProperties,
  main: {
    padding: 24,
    overflowY: "auto",
  } as React.CSSProperties,
};

export default function App() {
  const [params] = useSearchParams();
  const sessionId = params.get("session") ?? "";

  return (
    <div style={css.shell}>
      <header style={css.header}>
        <span style={{ color: "#58a6ff" }}>CodeScope</span>
        {sessionId && (
          <span style={{ color: "#8b949e", fontWeight: 400 }}>session: {sessionId}</span>
        )}
      </header>

      <nav style={css.sidebar}>
        {Object.entries(nav).map(([to, label]) => (
          <NavLink
            key={to}
            to={`${to}${sessionId ? `?session=${sessionId}` : ""}`}
            end={to === "/"}
            style={({ isActive }) => ({
              padding: "8px 20px",
              color: isActive ? "#e6edf3" : "#8b949e",
              background: isActive ? "#21262d" : "transparent",
              borderLeft: isActive ? "2px solid #58a6ff" : "2px solid transparent",
              fontSize: 13,
            })}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <main style={css.main}>
        <Routes>
          <Route path="/" element={<Dashboard sessionId={sessionId} />} />
          <Route path="/findings" element={<Findings sessionId={sessionId} />} />
          <Route path="/hotspots" element={<Hotspots sessionId={sessionId} />} />
          <Route path="/patterns" element={<Patterns />} />
        </Routes>
      </main>
    </div>
  );
}
