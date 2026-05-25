export interface SessionSummary {
  session_id: string;
  project_root: string;
  started_at: string;
  status: "running" | "complete";
  hotspot_count: number;
  finding_count: number;
  pattern_count: number;
  patterns_used: number;
}

export interface FindingInstance {
  file_path: string;
  line_start: number;
  line_end: number;
  description: string;
}

export interface AggregatedFinding {
  pattern_id: string;
  pattern_name: string;
  severity: "low" | "medium" | "high" | "critical";
  instance_count: number;
  file_count: number;
  fix_suggestion: string;
  instances: FindingInstance[];
}

export interface Pattern {
  id: string;
  name: string;
  category: string;
  language: string;
  severity: string;
  description: string;
  tags: string[];
  library: string;
}

export interface PatternDetail extends Pattern {
  ast_hints: Record<string, unknown>;
  prompt_supplement: string;
  fix_template: string;
  negative_examples: unknown[];
}

export type ProgressEvent =
  | { type: "progress"; stage: "ranking"; file_count: number }
  | { type: "progress"; stage: "analysing"; current: number; total: number; file: string }
  | { type: "complete"; session_id: string }
  | { type: "error"; message: string }
  | { type: "ping" };
