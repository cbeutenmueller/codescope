import { useEffect, useState } from "react";
import { api } from "../api";
import type { Pattern, PatternDetail } from "../types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#f85149",
  high: "#ff7b72",
  medium: "#d29922",
  low: "#3fb950",
};

export default function Patterns() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [selected, setSelected] = useState<PatternDetail | null>(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .patterns()
      .then((r) => setPatterns(r.patterns))
      .catch((e: Error) => setError(e.message));
  }, []);

  const filtered = patterns.filter(
    (p) =>
      !filter ||
      p.name.toLowerCase().includes(filter.toLowerCase()) ||
      p.tags.some((t) => t.includes(filter.toLowerCase())) ||
      p.language.includes(filter.toLowerCase())
  );

  const selectPattern = (p: Pattern) => {
    api
      .pattern(p.id)
      .then(setSelected)
      .catch((e: Error) => setError(e.message));
  };

  if (error) return <p style={{ color: "#f85149" }}>{error}</p>;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 20, height: "100%" }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
          <h2 style={{ fontSize: 18 }}>Patterns ({filtered.length})</h2>
          <input
            placeholder="Filter…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{
              padding: "6px 10px",
              fontSize: 13,
              background: "#0d1117",
              border: "1px solid #30363d",
              borderRadius: 6,
              color: "#e6edf3",
              outline: "none",
            }}
          />
        </div>

        <div
          style={{
            background: "#161b22",
            border: "1px solid #30363d",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          {filtered.map((p, i) => (
            <button
              key={p.id}
              onClick={() => selectPattern(p)}
              style={{
                width: "100%",
                padding: "10px 16px",
                borderTop: i > 0 ? "1px solid #21262d" : "none",
                background: selected?.id === p.id ? "#21262d" : "none",
                border: "none",
                color: "#e6edf3",
                cursor: "pointer",
                textAlign: "left",
                display: "flex",
                alignItems: "center",
                gap: 12,
                fontSize: 13,
              }}
            >
              <span
                style={{
                  color: SEVERITY_COLOR[p.severity] ?? "#8b949e",
                  fontSize: 10,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  minWidth: 52,
                }}
              >
                {p.severity}
              </span>
              <span style={{ flex: 1 }}>{p.name}</span>
              <span style={{ color: "#8b949e", fontSize: 11 }}>{p.language}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        {selected ? (
          <div
            style={{
              background: "#161b22",
              border: "1px solid #30363d",
              borderRadius: 8,
              padding: 20,
              fontSize: 13,
              position: "sticky",
              top: 0,
            }}
          >
            <p style={{ color: "#8b949e", fontSize: 11, marginBottom: 6 }}>{selected.id}</p>
            <h3 style={{ fontSize: 15, marginBottom: 12 }}>{selected.name}</h3>
            <p style={{ color: "#8b949e", lineHeight: 1.6, marginBottom: 16 }}>
              {selected.description}
            </p>
            {selected.fix_template && (
              <>
                <p style={{ color: "#3fb950", fontSize: 11, fontWeight: 700, marginBottom: 6 }}>
                  FIX
                </p>
                <pre
                  style={{
                    background: "#0d1117",
                    borderRadius: 6,
                    padding: 12,
                    fontSize: 12,
                    whiteSpace: "pre-wrap",
                    color: "#e6edf3",
                    marginBottom: 12,
                  }}
                >
                  {selected.fix_template}
                </pre>
              </>
            )}
            <p style={{ color: "#8b949e", fontSize: 11 }}>
              Tags: {selected.tags.join(", ")} &nbsp;|&nbsp; Library: {selected.library}
            </p>
          </div>
        ) : (
          <div
            style={{
              background: "#161b22",
              border: "1px solid #30363d",
              borderRadius: 8,
              padding: 20,
              color: "#8b949e",
              fontSize: 13,
            }}
          >
            Select a pattern to see details.
          </div>
        )}
      </div>
    </div>
  );
}
