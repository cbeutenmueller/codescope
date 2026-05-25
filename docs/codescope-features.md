# CodeScope — Feature List

> Review companion for senior developers and system architects.
> Priority: P0 must-have · P1 should-have · P2 nice-to-have
> Size: S (<1d) · M (1–3d) · L (3–7d) · XL (>1w)

---

## Epic 1 · Core Infrastructure

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 1.1 | `codescope init` — copy built-in patterns, generate config skeleton | P0 | S | |
| 1.2 | TOML config loader with validation and LLM profile support | P0 | M | |
| 1.3 | `uv`-based packaging, single `codescope` entry point | P0 | S | |
| 1.4 | Logging to file + stderr, configurable level | P0 | S | |
| 1.5 | Session persistence — save/load review sessions | P1 | M | enables resume + re-export |
| 1.6 | `.codescope/` project-local config overlay | P1 | S | repo-level defaults |

---

## Epic 2 · Hot Spot Ranker

The entry point for every review. Tells the reviewer where to look.

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 2.1 | Git signal extractor — change frequency, churn, recency per file | P0 | M | GitPython |
| 2.2 | Cyclomatic complexity per file via lizard | P0 | M | multi-language, no JVM |
| 2.3 | Size signal — LOC, method count, class count | P0 | S | from AST + wc |
| 2.4 | Dependency/coupling signal — import count, DI param count | P0 | M | from AST extractor |
| 2.5 | Hot spot scorer — weighted combination of signals | P0 | M | configurable weights |
| 2.6 | Hot spot ranker — top-N selection, configurable N | P0 | S | |
| 2.7 | Signal breakdown per file (show contribution of each signal) | P1 | S | for reviewer transparency |
| 2.8 | `codescope hotspots` — headless ranked list output | P1 | S | |
| 2.9 | Filter hot spots by language, path, signal threshold | P2 | M | |

---

## Epic 3 · AST Indexer

Structural pre-filter — narrows LLM focus to plausible pattern candidates.

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 3.1 | tree-sitter setup: Java + TypeScript grammars | P0 | M | |
| 3.2 | Java extractor: classes, methods, annotations, constructor params, imports | P0 | L | |
| 3.3 | TypeScript/Angular extractor: components, decorators, DI tokens, subscriptions | P0 | L | |
| 3.4 | Tantivy index: schema, write/query, persistence | P0 | L | |
| 3.5 | Full index build from project root with glob exclusions | P0 | M | |
| 3.6 | Incremental indexing via git-diff | P1 | M | |
| 3.7 | `codescope index` CLI with status + timing output | P1 | S | |

---

## Epic 4 · Pattern Library

The compounding institutional asset. Built-in smells + everything added during reviews.

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 4.1 | Pattern YAML schema + Pydantic validation | P0 | M | id, name, ast_hints, prompt_supplement, fix_template, negative_examples |
| 4.2 | AST hints translator — closed 13-type hint schema → tree-sitter / index queries | P0 | L | AND across keys, OR within lists |
| 4.3 | Pattern loader — discover + merge YAML files from patterns dir | P0 | M | |
| 4.4 | Built-in: `java_spring_context.yaml` | P0 | M | @Transactional private; @Async proxy; @Scheduled exception |
| 4.5 | Built-in: `java_spring_data.yaml` | P0 | M | Query in loop; N+1 in stream; EAGER on collections; missing readOnly |
| 4.6 | Built-in: `java_spring_security.yaml` | P0 | M | Redundant user lookup; SecurityContextHolder in service |
| 4.7 | Built-in: `java_architecture.yaml` | P0 | M | Layer violations; anemic domain; God service; over-injection |
| 4.8 | Built-in: `java_testing.yaml` | P0 | M | @SpringBootTest unit scope; missing @DirtiesContext; @MockBean in full context |
| 4.9 | Built-in: `angular_rxjs.yaml` | P0 | M | Subscription leaks; nested subscribe; Subject exposure |
| 4.10 | Built-in: `angular_lifecycle.yaml` | P0 | M | detectChanges in ngAfterViewInit; navigate in constructor; translate.instant |
| 4.11 | Built-in: `angular_architecture.yaml` | P0 | M | Smart/dumb violation; OnPush incompatibility; module isolation |
| 4.12 | Built-in: `angular_testing.yaml` | P1 | M | detectChanges before inputs; async guard misuse |
| 4.13 | `codescope patterns list` with tag filter | P0 | S | |
| 4.14 | `codescope patterns show <id>` — full pattern detail | P1 | S | |
| 4.15 | `codescope patterns edit <id>` — open in $EDITOR | P1 | S | |
| 4.16 | Pattern import script from IntelliJ community inspection metadata | P2 | L | high yield, one-time |

---

## Epic 5 · Interactive Pattern Creation

The mechanism that makes the library grow. Core differentiator.

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 5.1 | LLM-assisted pattern generator — plain language → draft YAML | P0 | L | prompt engineering is critical here |
| 5.2 | Pattern validator — run draft pattern against full index → instance count | P0 | M | the "found N more instances" moment |
| 5.3 | Pattern creation panel in Review page — describe → draft → edit → validate → save | P0 | L | |
| 5.4 | Pattern calibration — show all instances, let reviewer mark false positives | P1 | M | improves ast_hints over time |
| 5.5 | `codescope patterns new` — CLI entry point for interactive creation | P1 | S | |
| 5.6 | Session patterns — patterns created during a session, prompt to save at end | P1 | M | |
| 5.7 | Pattern sharing export — bundle custom patterns as a YAML archive | P2 | S | enables team sharing |

---

## Epic 6 · Pattern Library Distribution

Git as the distribution mechanism. No central registry.

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 6.1 | `[[pattern_libraries]]` config block: source, ref, auth | P0 | M | |
| 6.2 | Library manager: git clone + checkout on first use | P0 | M | to `~/.codescope/libraries/` |
| 6.3 | `codescope patterns update` — fetch + checkout for all unpinned libraries | P0 | M | pinned refs never auto-update |
| 6.4 | Pattern ID namespacing: `library-name/pattern-id` | P0 | M | prevents cross-library collision |
| 6.5 | Conflict resolution: later config entry wins, explicit overrides in config | P0 | S | |
| 6.6 | `codescope patterns add <git-url>` — add a new library source | P0 | S | |
| 6.7 | `codescope patterns libraries` — list sources + sync status + ref | P1 | S | |
| 6.8 | Pattern save destination selector during interactive creation | P0 | M | local / team / new |
| 6.9 | Commit to team library from pattern creation flow | P0 | M | git commit in local clone |
| 6.10 | `codescope patterns push <library>` — push local commits to remote | P1 | S | separate from commit step |
| 6.11 | Auth support: env var token, SSH key, credential helper passthrough | P1 | M | |
| 6.12 | Pattern library manifest (`library.yaml`): name, description, maintainer, tags | P2 | S | for discovery |
| 6.13 | `codescope patterns export` — bundle custom patterns as shareable archive | P2 | S | |

---



| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 6.1 | OpenAI SDK provider, configurable base_url + model | P0 | M | covers llama.cpp, Ollama, OpenAI, Azure |
| 6.2 | Named LLM profiles, `--profile` flag | P0 | S | |
| 6.3 | Prompt builder: hot spot context + pattern list + code chunks | P0 | L | token budget management |
| 6.4 | JSON response parser with graceful fallback | P0 | M | |
| 6.5 | Streaming response display via WebSocket in Review page | P1 | M | |
| 6.6 | Retry + backoff | P1 | S | |
| 6.7 | Token usage tracking, cost estimate for API providers | P2 | S | |

---

## Epic 7 · Analysis Runner

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 7.1 | Hot spot → pattern pre-filter → LLM → findings pipeline | P0 | L | |
| 7.2 | Token budget + chunking: whole-file vs method-level windowing | P0 | L | class context summary per chunk |
| 7.3 | Pattern grouping per chunk — one LLM call covers all matched patterns | P0 | M | |
| 7.4 | Finding dedup stage 1: merge overlapping instances within a file | P0 | M | |
| 7.5 | Finding aggregation stage 2: group by pattern, count, rank by frequency | P0 | M | frequency is the primary sort key |
| 7.6 | Per-finding fix suggestion surfaced from pattern's fix_template | P0 | S | |
| 7.7 | False positive feedback: write reviewer-marked FPs to pattern negative_examples | P0 | M | |
| 7.8 | Inject negative_examples into prompt on subsequent runs | P0 | S | self-calibration |
| 7.9 | Per-pattern rolling false-positive rate tracking | P1 | M | surfaces low-quality patterns |
| 7.10 | Health score calculation | P1 | S | |
| 7.11 | Scope filters: `--tags`, `--top N`, `--language`, `--level` | P1 | M | |
| 7.12 | `codescope review --no-server` headless mode | P0 | M | CI and scripted use |

---

## Epic 8 · Web UI

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 8.1 | FastAPI backend skeleton: routes, CORS, static file serving | P0 | M | serves built React app |
| 8.2 | WebSocket endpoint for streaming LLM output to frontend | P0 | M | |
| 8.3 | React app skeleton: routing, API client, dark theme | P0 | M | |
| 8.4 | **Hot Spots page**: ranked file list, signal breakdown bars per file | P0 | L | entry point for every review |
| 8.5 | **Review page**: Monaco code viewer + findings panel side-by-side | P0 | XL | core workspace |
| 8.6 | Inline code annotations in Monaco at finding locations | P0 | L | |
| 8.7 | Findings sorted by frequency across session, not per-file | P0 | M | key UX decision |
| 8.8 | Finding detail: pattern name, instance count, fix suggestion | P0 | M | |
| 8.9 | New pattern trigger from review page → PatternCreate flow | P0 | M | must be frictionless |
| 8.10 | **Pattern Create page**: describe → LLM draft → edit → validate → save to library | P0 | L | |
| 8.11 | Pattern destination selector: local / team library / new | P0 | M | |
| 8.12 | **Patterns page**: library browser, per-library grouping, enable/disable | P1 | L | |
| 8.13 | **Report page**: systematic findings preview, export buttons | P1 | L | |
| 8.14 | Navigate hot spots with prev/next without losing review context | P1 | M | |
| 8.15 | `codescope review` launches server + opens browser automatically | P0 | S | |
| 8.16 | PyWebView desktop packaging — native window wrapping web UI | P2 | M | same frontend, no code change |
| 8.17 | Tauri desktop packaging — smaller binary, better system integration | P2 | L | Rust toolchain required |

---

## Epic 9 · Review Report

The primary deliverable. Structured for handing to a team lead.

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 9.1 | Report structure: executive summary, systematic findings, hot spot table | P0 | L | |
| 9.2 | Systematic findings ranked by frequency with all instances listed | P0 | M | |
| 9.3 | Per-finding fix section with fix_template from pattern | P0 | M | |
| 9.4 | Hot spot analysis table (top N files, signals breakdown) | P0 | M | |
| 9.5 | Pattern library section: patterns used, patterns created this session | P1 | S | |
| 9.6 | Markdown output | P0 | M | |
| 9.7 | HTML output — self-contained, dark theme, collapsible sections | P1 | L | |
| 9.8 | Code Climate JSON — GitLab MR inline display | P1 | M | |
| 9.9 | GitLab Issues — one issue per systematic pattern (not per instance) | P2 | L | |
| 9.10 | GitHub Issues | P2 | L | |
| 9.11 | Jira | P2 | L | |
| 9.12 | `codescope export` — re-export from saved session | P1 | M | |

---

---

## Epic 10 · CI / Developer Experience

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 10.1 | Exit codes: 0 clean, 1 findings above threshold, 2 error | P0 | S | |
| 10.2 | `--fail-on <severity>` for CI gating | P1 | S | |
| 10.3 | Docker image for headless/CI use | P1 | M | |
| 10.4 | GitLab CI example — run CodeScope headless, upload report as artifact | P1 | M | |
| 10.5 | Machine-readable JSON stdout (`--output-format json`) | P1 | S | |

---

## Epic 11 · Documentation

| # | Feature | Priority | Size | Notes |
|---|---|---|---|---|
| 11.1 | README: premise, quickstart, config reference | P0 | M | |
| 11.2 | Pattern authoring guide — how to write effective ast_hints and prompt_supplement | P1 | M | |
| 11.3 | Built-in smell catalogue — one page per pattern with examples | P1 | L | |
| 11.4 | CI integration guide | P2 | M | |

---

## Milestone Grouping

### M1 — Headless Reviewer (proves the core loop)
Hot spot ranking + pattern matching + LLM + markdown report, no web UI.
Epics: 1, 2, 3, 4 (4.1–4.12), 7, 9 (9.1–9.6)
**Exit condition:** run on a real Spring Boot codebase, produce a useful report.

### M2 — Web UI (the review experience)
Full interactive review session in the browser with Monaco code viewer.
Epics: 8 (8.1–8.15), 9.7–9.8
**Exit condition:** complete a real review session in the browser without touching the CLI.

### M3 — Interactive Pattern Creation + Library Distribution (the differentiator)
Pattern creation loop + Git-based library sharing.
Epics: 5 (5.1–5.6), 6 (6.1–6.10)
**Exit condition:** describe a smell, find all instances in 60 seconds, push to team library.

### M4 — Distribution + Packaging
CI integration, Docker, desktop packaging.
Epics: 10, 11, 8.16–8.17
**Exit condition:** plugs into an existing GitLab pipeline; downloadable desktop app.

### M5 — Pattern Depth + Ecosystem
Angular test patterns, IntelliJ import, full issue tracker adapters, VS Code extension.
Epics: 4.16, 5.7, 9.9–9.11, remaining P2 features
