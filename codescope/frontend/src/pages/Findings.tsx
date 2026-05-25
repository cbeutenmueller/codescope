import { useEffect, useState } from "react";
import { api } from "../api";
import type { AggregatedFinding } from "../types";

interface Props {
  sessionId: string;
}

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#f85149",
  high: "#ff7b72",
  medium: "#d29922",
  low: "#3fb950",
};

export default function Findings({ sessionId }: Props) {
  const [findings, setFindings] = useState<AggregatedFinding[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sessionId) return;
    api
      .findings(sessionId)
      .then((r) => setFindings(r.findings))
      .catch((e: Error) => setError(e.message));
  }, [sessionId]);

  if (!sessionId) return <p style={{ color: "#8b949e" }}>No session selected.</p>;
  if (error) return <p style={{ color: "#f85149" }}>{error}</p>;
  if (!findings.length) return <p style={{ color: "#8b949e" }}>No findings.</p>;

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  return (
    <div>
      <h2 style={{ fontSize: 18, marginBottom: 20 }}>
        Findings ({findings.length} pattern{findings.length !== 1 ? "s" : ""})
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {findings.map((f) => (
          <div
            key={f.pattern_id}
            style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8 }}
          >
            <button
              onClick={() => toggle(f.pattern_id)}
              style={{
                width: "100%",
                padding: "14px 16px",
                display: "flex",
                alignItems: "center",
                gap: 12,
                background: "none",
                border: "none",
                color: "#e6edf3",
                cursor: "pointer",
                textAlign: "left",
                fontSize: 14,
              }}
            >
              <span
                style={{
                  color: SEVERITY_COLOR[f.severity] ?? "#8b949e",
                  fontWeight: 700,
                  minWidth: 60,
                  fontSize: 11,
                  textTransform: "uppercase",
                }}
              >
                {f.severity}
              </span>
              <span style={{ flex: 1, fontWeight: 600 }}>{f.pattern_name}</span>
              <span style={{ color: "#8b949e", fontSize: 12 }}>
                {f.instance_count} instance{f.instance_count !== 1 ? "s" : ""} in {f.file_count}{" "}
                file{f.file_count !== 1 ? "s" : ""}
              </span>
              <span style={{ color: "#8b949e" }}>{expanded.has(f.pattern_id) ? "▲" : "▼"}</span>
            </button>

            {expanded.has(f.pattern_id) && (
              <div style={{ borderTop: "1px solid #30363d", padding: "14px 16px" }}>
                {f.fix_suggestion && (
                  <p style={{ color: "#8b949e", fontSize: 13, marginBottom: 12 }}>
                    {f.fix_suggestion}
                  </p>
                )}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {f.instances.map((inst, i) => (
                    <div
                      key={i}
                      style={{
                        background: "#0d1117",
                        borderRadius: 6,
                        padding: "10px 14px",
                        fontSize: 12,
                      }}
                    >
                      <span style={{ color: "#58a6ff" }}>
                        {inst.file_path}:{inst.line_start}
                        {inst.line_end !== inst.line_start ? `–${inst.line_end}` : ""}
                      </span>
                      {inst.description && (
                        <p style={{ color: "#8b949e", marginTop: 4 }}>{inst.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
