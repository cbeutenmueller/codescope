import { useEffect, useState } from "react";
import { api } from "../api";

interface Props {
  sessionId: string;
}

export default function Hotspots({ sessionId }: Props) {
  const [hotspots, setHotspots] = useState<string[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sessionId) return;
    api
      .hotspots(sessionId)
      .then((r) => setHotspots(r.hotspots))
      .catch((e: Error) => setError(e.message));
  }, [sessionId]);

  if (!sessionId) return <p style={{ color: "#8b949e" }}>No session selected.</p>;
  if (error) return <p style={{ color: "#f85149" }}>{error}</p>;

  return (
    <div>
      <h2 style={{ fontSize: 18, marginBottom: 20 }}>
        Hotspots ({hotspots.length} file{hotspots.length !== 1 ? "s" : ""})
      </h2>
      <div
        style={{
          background: "#161b22",
          border: "1px solid #30363d",
          borderRadius: 8,
          overflow: "hidden",
        }}
      >
        {hotspots.length === 0 ? (
          <p style={{ padding: 16, color: "#8b949e", fontSize: 13 }}>No hotspots found.</p>
        ) : (
          hotspots.map((path, i) => (
            <div
              key={path}
              style={{
                padding: "10px 16px",
                fontSize: 13,
                borderTop: i > 0 ? "1px solid #21262d" : "none",
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <span style={{ color: "#8b949e", minWidth: 28, textAlign: "right" }}>
                {i + 1}
              </span>
              <span style={{ color: "#58a6ff", fontFamily: "inherit" }}>{path}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
