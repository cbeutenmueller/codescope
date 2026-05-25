# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeScope is a code review companion for senior developers and architects. It finds framework-semantic smells that syntax checkers cannot see (e.g., Spring proxy bypass, Angular subscription leaks) by combining hot spot ranking with an LLM-assisted pattern library. Target accuracy is 70–80% — it is a reviewer aid, not a CI gate.

See `docs/codescope-spec.md` for the full architecture spec and `docs/codescope-features.md` for the prioritized feature list and milestone grouping.

## Development Commands

This project uses [uv](https://docs.astral.sh/uv/) for package management (Python 3.13).

```bash
# Install dependencies
uv sync

# Run the app
uv run python main.py

# Run a single test
uv run pytest tests/test_hotspot_scorer.py

# Run all tests
uv run pytest

# Add a dependency
uv add <package>
```

## Planned Architecture

The codebase does not yet exist beyond the stub `main.py`. All module paths below come from `docs/codescope-spec.md`.

```
codescope/
├── cli.py                     # Entry point: init, index, review, export, patterns
├── server/                    # FastAPI backend (serves React build as static files)
│   ├── app.py
│   ├── routes/                # review, patterns, libraries, export
│   └── websockets.py          # Streaming LLM output to frontend
├── frontend/                  # React + TypeScript app
│   └── src/
│       ├── pages/             # HotSpots, Review, PatternCreate, Patterns, Report
│       └── components/        # CodeViewer (Monaco), HotspotBar, FindingCard
├── hotspot/                   # Hot spot ranking layer
│   ├── scorer.py              # hotspot_score formula (see below)
│   ├── ranker.py              # Top-N selection
│   └── signals/               # git.py, complexity.py, size.py, coupling.py
├── indexer/                   # Structural index (tree-sitter + Tantivy)
│   ├── ast_extractor.py
│   ├── index.py               # Tantivy schema + CRUD
│   └── languages/             # java.py, typescript.py
├── patterns/                  # Pattern library
│   ├── schema.py              # Pattern dataclass
│   ├── generator.py           # LLM-assisted YAML creation from plain language
│   ├── validator.py           # Run pattern → count instances
│   ├── library_manager.py     # Git clone/fetch per library source
│   └── builtin/               # YAML smell libraries (Spring Boot + Angular)
├── llm/                       # LLM provider (OpenAI SDK with configurable base_url)
├── analysis/                  # runner.py, finding.py, aggregator.py, session.py
└── output/                    # review_report, markdown, html, code_climate, adapters/
```

## Key Concepts

**Hot spot scoring formula:**
```
hotspot_score = change_frequency × log(1 + cyclomatic_complexity)
              × log(1 + dependency_count) × recency_weight
```
The LLM is only called on top-N hot spots (default 20). Weights are configurable in TOML config.

**Pattern YAML schema** — patterns have `id`, `name`, `severity`, `language`, `ast_hints`, `prompt_supplement`, `fix_template`, `negative_examples`, and `tags`. `ast_hints` is the structural pre-filter (13 supported hint types, AND across keys, OR within a list). The hint set is intentionally closed — new hint types require a schema version bump.

**Pattern namespacing** — IDs are prefixed with library name (`builtin/spring-data-2`, `myteam/user-lookup-1`). Later config entries win on conflict; `local` always appended last.

**Chunking strategy** — files within `max_tokens_per_call` (default 6000) are sent whole. Larger files are chunked at method level, each chunk carrying a class context summary (name, annotations, field declarations, all method signatures).

**Finding deduplication** — stage 1: merge overlapping instances within a file by `(pattern_id, file_path, overlapping_line_range)`; stage 2: aggregate by `pattern_id` across codebase, rank by `frequency` descending.

**False positive loop** — reviewer-marked false positives are appended to the pattern's `negative_examples` YAML field, which are injected into the prompt on subsequent runs.

## Technology Stack

| Concern | Library |
|---|---|
| Backend | FastAPI + WebSockets |
| Frontend | React + TypeScript + Monaco Editor |
| AST parsing | tree-sitter (py-tree-sitter), Java + TypeScript grammars |
| Local index | Tantivy via `tantivy-py` |
| Git signals | GitPython |
| Complexity | lizard |
| LLM client | openai-python SDK (configurable `base_url` for llama.cpp, Ollama, OpenAI, Azure) |
| Config | TOML |
| Patterns | YAML (Git-distributed) |
| Packaging | uv + PyInstaller |

## Milestone Plan

- **M1** — Headless reviewer (hot spot ranking + pattern matching + LLM + markdown report, no web UI)
- **M2** — Web UI (interactive browser session with Monaco)
- **M3** — Interactive pattern creation + Git-based library distribution
- **M4** — CI integration, Docker, desktop packaging
- **M5** — Pattern depth and ecosystem
