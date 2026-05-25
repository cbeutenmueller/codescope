# CodeScope

> A review companion for senior developers and system architects.  
> Finds the framework-semantic smells that syntax checkers can't see.  
> Gets smarter with every engagement.

---

## What it does

When a senior engineer reviews an unfamiliar codebase, they do two things: find where the risk is concentrated, then identify the patterns behind it. CodeScope automates both steps.

It is **not a linter**. It does not gate CI. It aims to give a reviewer a ranked list of hot spots and a growing library of team-specific smells — before they read the first file.

**Target accuracy: 70–80%.** A false positive the reviewer dismisses in 30 seconds is acceptable. Missing a pattern that appears 11 times across the codebase is not.

---

## How it works

```
codescope review
       │
       ▼
 HOT SPOT RANKER          — change frequency × complexity × coupling × recency
       │
       ▼
 PATTERN PRE-FILTER       — AST hints narrow files to plausible candidates
       │
       ▼
 LLM SEMANTIC ANALYSIS    — one call per chunk, all matched patterns at once
       │
       ▼
 FINDING DEDUPLICATION    — merge overlapping instances, group by pattern
       │
       ▼
 REVIEW REPORT            — systematic findings ranked by frequency
```

The LLM is only called on the top-N hot spots (default 20). Token usage stays bounded and analysis focuses where it matters.

---

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/your-username/codescope
cd codescope
uv sync
```

Point it at a project:

```bash
cd /path/to/your/project
codescope init          # creates .codescope/config.toml
codescope index         # builds the structural index
codescope review        # runs the analysis, prints findings
```

---

## CLI

```bash
# Initialise CodeScope in the current project
codescope init

# Build (or incrementally update) the structural index
codescope index [--full]

# Run a review session
codescope review [--output report.md] [--tags spring-data,spring-security]
codescope review --top 10                  # review top 10 hot spots only
codescope review --profile openai          # use a named LLM profile
codescope review --no-server               # headless mode (CI / scripted)

# Re-export a saved session
codescope export [--session <id>] [--output report.md]

# Pattern library
codescope patterns list [--tag spring] [--library myteam]
codescope patterns show builtin/spring-data-1
```

---

## Configuration

`codescope init` creates `.codescope/config.toml` in your project. Edit it to point at your LLM:

```toml
[llm]
base_url = "https://api.openai.com/v1"
model    = "gpt-4o-mini"
api_key  = "sk-YOUR-KEY-HERE"
timeout  = 120

# Named profiles — switch with: codescope review --profile local
[llm.profiles.local]
base_url = "http://localhost:11434/v1"
model    = "qwen3-30b"
api_key  = "sk-local"

[review]
top_n_hotspots  = 20
max_tokens_per_call = 6000

[review.hotspot_weights]
change_frequency = 1.0
complexity       = 0.8
dependencies     = 0.6
recency          = 0.4

[index]
languages     = ["java", "typescript"]
exclude_globs = ["**/generated/**", "**/target/**", "**/node_modules/**"]

[[pattern_libraries]]
name   = "builtin"
source = "builtin"

[[pattern_libraries]]
name   = "myteam"
source = "https://gitlab.myorg.com/architecture/codescope-patterns"
ref    = "main"
auth   = "env:GITLAB_TOKEN"

[[pattern_libraries]]
name   = "local"
source = "~/.codescope/patterns"
```

User-level defaults live in `~/.codescope/config.toml`. Project config is merged on top.

---

## Built-in pattern library

CodeScope ships with 16 patterns targeting smells that require runtime framework knowledge — undetectable by any rule-based static analyser.

| Library file | Focus |
|---|---|
| `java_spring_data` | Query in loop/stream (N+1), missing `readOnly=true`, `FetchType.EAGER` on collections |
| `java_spring_context` | `@Transactional` on private methods, self-invocation proxy bypass, `@Async` proxy bypass |
| `java_spring_security` | Redundant user lookup via repository, `SecurityContextHolder` in service layer |
| `java_architecture` | Controller→repository direct coupling, constructor over-injection, anemic domain model |
| `angular_rxjs` | Subscription leaks, nested subscribe, Subject exposed as Observable |
| `angular_architecture` | Missing `OnPush`, smart logic in dumb components |

### Hot spot scoring

Files are ranked before any LLM call:

```
hotspot_score = (change_frequency × w₁) × log(1 + complexity × w₂)
              × log(1 + dependencies × w₃) × (recency × w₄)
```

Weights are configurable per project. A file never changed scores 0 — not a hot spot.

### Pattern YAML schema

Patterns are plain YAML, version-controllable, and shareable via Git:

```yaml
- id: spring-data-1
  name: Query Inside Loop or Stream
  category: spring-data
  language: java
  severity: high
  description: >
    A repository method is called inside a loop or stream map, causing N+1 queries.
  ast_hints:
    contains_construct: [loop, stream_map]
    method_call_pattern: ["*Repository.find*"]
  prompt_supplement: >
    Look for repository calls inside for loops or stream .map() lambdas.
  fix_template: >
    Collect all IDs first, then use findAllById() in a single query.
  tags: [spring-data, performance, n-plus-one]
  enabled: true
```

### Pattern library distribution

Libraries are Git repositories — no central registry, no package manager:

```toml
[[pattern_libraries]]
name   = "spring-community"
source = "https://github.com/codescope-community/spring-patterns"
ref    = "v1.2.0"       # pinned — patterns don't shift under a review
```

Team patterns stay in your own infrastructure. Local patterns always win on conflict.

---

## Development

```bash
# Install all dependencies including dev tools
uv sync --extra dev

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_hotspot_scorer.py

# Format code
uv run black .

# Check formatting (what CI runs)
uv run black --check .
```

### Project structure

```
codescope/
├── cli.py                  # Entry point: init, index, review, export, patterns
├── config.py               # TOML config loading + Pydantic models
├── hotspot/                # Hot spot ranking: git + complexity + size + coupling
├── patterns/               # Pattern schema, YAML loader, namespacing, built-ins
├── llm/                    # OpenAI SDK provider, prompt builder, response parser
├── analysis/               # Finding dataclasses, dedup/aggregation, session persistence
├── indexer/                # File walker, SQLite index, Java + TypeScript extractors
└── output/                 # Markdown report renderer
tests/
├── fixtures/               # Sample Java and Angular files for tests
└── test_*.py               # 70 tests across all modules
```

### CI

GitHub Actions runs on every push and pull request to `main`:

- **Format check** — `black --check .`
- **Tests** — `pytest`

---

## Roadmap

| Milestone | Focus |
|---|---|
| **M1** (current) | Headless reviewer — hot spot ranking + pattern matching + LLM + markdown report |
| **M2** | Web UI — FastAPI + React + Monaco code viewer, side-by-side code and findings |
| **M3** | Interactive pattern creation + Git-based library distribution |
| **M4** | CI integration, Docker image, desktop packaging (PyWebView / Tauri) |
| **M5** | Pattern depth, VS Code extension, issue tracker adapters |

---

## License

[MIT](LICENSE) © 2026 Christian Beutenmueller
