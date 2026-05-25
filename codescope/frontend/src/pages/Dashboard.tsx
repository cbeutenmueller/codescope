import { useEffect, useState } from "react";
import { api } from "../api";
import type { SessionSummary } from "../types";

interface Props {
  sessionId: string;
}

const card = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: 8,
  padding: 20,
} as React.CSSProperties;

const stat = {
  fontSize: 32,
  fontWeight: 700,
  color: "#58a6ff",
  lineHeight: 1,
} as React.CSSProperties;

const label = {
  fontSize: 12,
  color: "#8b949e",
  marginTop: 6,
} as React.CSSProperties;

export default function Dashboard({ sessionId }: Props) {
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sessionId) return;
    api
      .session(sessionId)
      .then(setSession)
      .catch((e: Error) => setError(e.message));
  }, [sessionId]);

  if (!sessionId)
    return (
      <p style={{ color: "#8b949e" }}>
        No session selected. Start a review with{" "}
        <code style={{ color: "#58a6ff" }}>codescope review</code>.
      </p>
    );

  if (error) return <p style={{ color: "#f85149" }}>{error}</p>;
  if (!session) return <p style={{ color: "#8b949e" }}>Loading…</p>;

  const cards = [
    { value: session.hotspot_count, label: "Hotspots" },
    { value: session.pattern_count, label: "Patterns hit" },
    { value: session.finding_count, label: "Instances" },
    { value: session.patterns_used, label: "Patterns run" },
  ];

  return (
    <div>
      <h2 style={{ fontSize: 18, marginBottom: 20 }}>Review Summary</h2>
      <p style={{ color: "#8b949e", fontSize: 13, marginBottom: 24 }}>
        Project: <span style={{ color: "#e6edf3" }}>{session.project_root}</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;Started: {new Date(session.started_at).toLocaleString()}
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
        {cards.map((c) => (
          <div key={c.label} style={card}>
            <div style={stat}>{c.value}</div>
            <div style={label}>{c.label}</div>
          </div>
        ))}
      </div>

      {session.finding_count > 0 && (
        <p style={{ marginTop: 28, color: "#8b949e", fontSize: 13 }}>
          Navigate to <strong>Findings</strong> to see detailed results, or{" "}
          <a href={`/api/export/${sessionId}/markdown`} download>
            download the Markdown report
          </a>
          .
        </p>
      )}
    </div>
  );
}
