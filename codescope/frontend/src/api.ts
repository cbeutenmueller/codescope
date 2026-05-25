import type { SessionSummary, AggregatedFinding, Pattern, PatternDetail } from "./types";

const BASE = "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  session: (id: string) => get<SessionSummary>(`/api/review/${id}`),
  findings: (id: string) => get<{ findings: AggregatedFinding[] }>(`/api/review/${id}/findings`),
  hotspots: (id: string) => get<{ hotspots: string[] }>(`/api/review/${id}/hotspots`),
  patterns: (opts?: { tag?: string; library?: string }) => {
    const params = new URLSearchParams();
    if (opts?.tag) params.set("tag", opts.tag);
    if (opts?.library) params.set("library", opts.library);
    const qs = params.size ? `?${params}` : "";
    return get<{ patterns: Pattern[] }>(`/api/patterns${qs}`);
  },
  pattern: (id: string) => get<PatternDetail>(`/api/patterns/${id}`),
  exportMarkdown: (id: string) => fetch(`/api/export/${id}/markdown`).then((r) => r.text()),
};
