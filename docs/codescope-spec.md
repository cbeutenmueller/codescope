# CodeScope — Architecture Specification

> A review companion for senior developers and system architects.
> Finds the framework-semantic smells that syntax checkers can't see.
> Gets smarter with every engagement.

---

## Premise

When a senior engineer reviews an unfamiliar codebase, they do two things:
find where the risk is concentrated, then identify the patterns behind it.
Both steps are currently manual. CodeScope automates them.

It is not a linter. It does not gate CI. It does not aim for 100% precision.
It aims to give a reviewer a hypothesis — ranked hot spots, known anti-patterns,
and a growing library of team-specific smells — before they read the first file.

**Target accuracy: 70–80%.** A false positive the reviewer dismisses in
30 seconds is acceptable. Missing a pattern that appears 11 times across the
codebase is not.

---

## The Three Problems It Solves

**1. Where do I look?**
Hot spot ranking combines change frequency, cyclomatic complexity, size, and
dependency count into a single risk signal. The reviewer starts with the
files that are complex, highly coupled, and actively changing — not a random
walk through the tree.

**2. What am I looking for?**
A pattern library of framework-semantic smells: things that require knowing
what Spring or Angular does at runtime, not just what the code says. Smells
that SonarQube, SpotBugs, and Semgrep fundamentally cannot detect because
they require reasoning about framework behavior, not syntax.

**3. How do I encode what I found?**
As the reviewer works, they spot new patterns the library doesn't know yet.
They describe them in plain language. The LLM formalizes them into a YAML
pattern entry, runs it immediately across the full codebase, and shows
how many more instances exist. The library grows. The next engagement starts
with more knowledge than the last.

---

## Core Flow

```
                    ┌─────────────────────────────┐
                    │   codescope review start     │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       HOT SPOT RANKER        │
                    │                              │
                    │  change frequency (git)      │
                    │  × cyclomatic complexity     │
                    │  × size (LOC, method count)  │
                    │  × dependency count          │
                    │                              │
                    │  → ranked list: top N files  │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     PATTERN LIBRARY RUN      │
                    │                              │
                    │  AST pre-filter per pattern  │
                    │  → focused code chunks       │
                    │  → LLM semantic analysis     │
                    │  → findings with frequency   │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     REVIEW SESSION (web UI)  │
                    │                              │
                    │  hot spot view               │
                    │  findings by pattern freq    │
                    │  ↕ interactive pattern       │
                    │    creation & validation     │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │       REVIEW REPORT          │
                    │                              │
                    │  executive summary           │
                    │  systematic findings ranked  │
                    │  by frequency + instances    │
                    │  suggested fix per pattern   │
                    └─────────────────────────────┘
```

---

## Technology Stack

| Concern | Choice | Rationale |
|---|---|---|
| Backend | **FastAPI** + **WebSockets** | Async, streaming-native, serves React build as static |
| Frontend | **React** + **TypeScript** | Monaco for code viewing, runs in browser or WebView |
| Code viewer | **Monaco Editor** | Inline annotations, syntax highlighting, read-only mode |
| AST parsing | **tree-sitter** (py-tree-sitter) | Java + TypeScript, single API, structural queries |
| Local index | **Tantivy** via `tantivy-py` | Rust core, Lucene query syntax, fast incremental |
| Git signals | **GitPython** | Change frequency, recency, author concentration |
| Complexity | **lizard** | Multi-language cyclomatic complexity, no JVM |
| LLM client | **openai-python** SDK | `base_url` override: llama.cpp, Ollama, OpenAI, Azure |
| Config | **TOML** | Human-editable, version-controllable |
| Patterns | **YAML** (Git-distributed) | Libraries sourced from any Git repo, namespaced |
| Desktop packaging | **PyWebView** / **Tauri** | Wraps existing web UI, no Electron overhead |
| Packaging | **uv** + **PyInstaller** | Python env + optional single-binary desktop build |

---

## Project Structure

```
codescope/
├── pyproject.toml
├── codescope/
│   ├── __main__.py
│   ├── cli.py                        # init, index, review, export, patterns
│   │
│   ├── server/                       # ← FastAPI backend
│   │   ├── app.py                    # FastAPI app, CORS, static file serving
│   │   ├── routes/
│   │   │   ├── review.py             # session start, hot spots, findings stream
│   │   │   ├── patterns.py           # CRUD + create + validate
│   │   │   ├── libraries.py          # add, update, push, list
│   │   │   └── export.py             # report generation + download
│   │   └── websockets.py             # streaming LLM output to frontend
│   │
│   ├── frontend/                     # ← React app (built to server/static/)
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── pages/
│   │   │   │   ├── HotSpots.tsx      # ranked file list, signal breakdown
│   │   │   │   ├── Review.tsx        # core workspace: code + findings side-by-side
│   │   │   │   ├── PatternCreate.tsx # interactive pattern creation
│   │   │   │   ├── Patterns.tsx      # library browser
│   │   │   │   └── Report.tsx        # report preview + export
│   │   │   └── components/
│   │   │       ├── CodeViewer.tsx    # Monaco editor, read-only, inline annotations
│   │   │       ├── HotspotBar.tsx
│   │   │       ├── FindingCard.tsx
│   │   │       └── FrequencySummary.tsx
│   │   └── package.json
│   │
│   ├── hotspot/                      # ← Hot spot ranking layer
│   │   ├── scorer.py                 # Combines signals → hotspot_score
│   │   ├── ranker.py                 # Top-N selection, configurable weights
│   │   └── signals/
│   │       ├── git.py                # Change frequency, recency, churn
│   │       ├── complexity.py         # Cyclomatic via lizard
│   │       ├── size.py               # LOC, method count, class count
│   │       └── coupling.py           # Import count, DI dependency count
│   │
│   ├── indexer/                      # ← Structural index layer
│   │   ├── walker.py                 # File scan, language detection
│   │   ├── ast_extractor.py          # tree-sitter → structural facts
│   │   ├── index.py                  # Tantivy schema + CRUD
│   │   ├── languages/
│   │   │   ├── java.py               # Classes, methods, annotations, param counts
│   │   │   └── typescript.py         # Components, decorators, DI tokens, subscriptions
│   │   └── incremental.py            # git-diff delta indexing
│   │
│   ├── patterns/                     # ← Pattern library
│   │   ├── loader.py                 # Discover + merge patterns from all libraries
│   │   ├── schema.py                 # Pattern dataclass (namespaced id)
│   │   ├── generator.py              # LLM-assisted pattern creation from plain language
│   │   ├── validator.py              # Run pattern → count instances → calibrate
│   │   ├── library_manager.py        # Git clone/fetch/checkout per library source
│   │   ├── namespace.py              # ID prefixing, conflict resolution, overrides
│   │   └── builtin/
│   │       ├── java_spring_context.yaml     # Proxy, transaction, async pitfalls
│   │       ├── java_spring_data.yaml        # Query, N+1, fetch strategy smells
│   │       ├── java_spring_security.yaml    # Principal misuse, auth smells
│   │       ├── java_architecture.yaml       # Layer violations, DDD smells
│   │       ├── java_testing.yaml            # Spring test misuse, test isolation
│   │       ├── angular_lifecycle.yaml       # Lifecycle hook misuse, CD issues
│   │       ├── angular_rxjs.yaml            # Subscription leaks, pipe patterns
│   │       ├── angular_architecture.yaml    # Module, state, smart/dumb smells
│   │       └── angular_testing.yaml         # Fixture, async, input testing smells
│   │
│   ├── llm/
│   │   ├── provider.py               # OpenAI SDK, configurable base_url + model
│   │   ├── prompt_builder.py         # Pattern + chunk + hot spot context → prompt
│   │   └── response_parser.py        # JSON extraction, graceful fallback
│   │
│   ├── analysis/
│   │   ├── runner.py                 # Hot spot → pattern match → LLM → findings
│   │   ├── finding.py                # Finding dataclass: pattern, severity, location, fix
│   │   ├── aggregator.py             # Group by pattern, count instances, rank by freq
│   │   └── session.py                # Persist review sessions to ~/.codescope/sessions/
│   │
│   └── output/
│       ├── base.py
│       ├── review_report.py          # Primary: structured review document
│       ├── markdown.py
│       ├── html.py
│       ├── code_climate.py           # GitLab MR inline display
│       └── adapters/
│           ├── gitlab.py
│           ├── github.py
│           └── jira.py
│
└── tests/
    ├── fixtures/
    │   ├── java/                     # Sample snippets per smell category
    │   └── angular/
    ├── test_hotspot_scorer.py
    ├── test_pattern_library.py
    ├── test_pattern_generator.py
    └── test_aggregator.py
```

---

## Hot Spot Scoring

Files are ranked before any LLM call is made. The scorer combines four signals:

```
hotspot_score = change_frequency × log(1 + cyclomatic_complexity)
              × log(1 + dependency_count) × recency_weight
```

| Signal | Source | What it indicates |
|---|---|---|
| `change_frequency` | `git log --follow` | Instability; frequently changed files carry more risk |
| `cyclomatic_complexity` | lizard | Internal complexity; harder to reason about |
| `dependency_count` | AST import/DI analysis | Coupling; many dependencies = many responsibilities |
| `recency_weight` | Last commit date | Recent changes matter more than ancient stable code |

The LLM is only called on top-N hot spots (configurable, default 20).
This keeps token usage bounded and focuses analysis where it matters.

**Signal weights are configurable.** A team optimising for stability
can weight `change_frequency` higher. A legacy codebase review might
weight `complexity` higher instead.

---

## Pattern Library Schema

Patterns are the durable institutional asset of the tool. They are YAML files,
version-controllable, and editable by anyone on the team.

```yaml
# ~/.codescope/patterns/java_spring_security.yaml

- id: spring-sec-1
  name: Unnecessary User Lookup via Repository
  category: spring-security
  language: java
  severity: medium
  description: >
    Controller fetches a User entity by ID when the authenticated principal
    is already available via Spring Security. Adds a redundant DB query on
    every request. Leaks the assumption that users are fetched by ID rather
    than by the security context.
  ast_hints:
    annotations_present: ["@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping"]
    method_call_pattern: ["*UserRepository.find*", "*userService.findById*"]
    parameter_type_absent: ["Authentication", "Principal", "@AuthenticationPrincipal"]
  prompt_supplement: >
    Look for controller methods that call a user repository or user service
    to fetch the current user by ID, when Spring Security's authenticated
    principal is already available as an injectable parameter.
    Ignore cases where a *different* user is being looked up (admin operations).
  fix_template: >
    Inject the authenticated user directly:
    public ResponseEntity<?> handle(@AuthenticationPrincipal UserDetails user) {
      // user is already available — no repository call needed
    }
  tags: [spring-security, performance, spring-mvc]
  enabled: true
```

**Key fields:**
- `ast_hints` — structural pre-filter before LLM call; keeps context focused
- `prompt_supplement` — guides LLM reasoning for this specific smell
- `fix_template` — canonical correct version; shown in findings and report
- `tags` — used for scoping a review session to a specific concern

### AST Hints — Formal Schema

`ast_hints` is the structural pre-filter. A file becomes a candidate for a pattern
only if it satisfies the hints. The supported hint types are fixed — each maps to
either a tree-sitter query or an index query.

| Hint key | Type | Match semantics |
|---|---|---|
| `node_type` | string | tree-sitter node kind must be present (e.g. `constructor_declaration`) |
| `annotations_present` | list[string] | at least one annotation in the list appears |
| `annotations_absent` | list[string] | none of the listed annotations appear |
| `method_call_pattern` | list[glob] | a call matching any glob appears (e.g. `*Repository.find*`) |
| `parameter_type_present` | list[string] | a parameter of one of these types exists |
| `parameter_type_absent` | list[string] | no parameter of these types exists |
| `class_instantiation` | list[string] | `new X()` for any listed type appears |
| `min_param_count` | int | a method/constructor with ≥ N parameters exists |
| `max_param_count` | int | a method/constructor with ≤ N parameters exists |
| `contains_construct` | list[enum] | body contains `loop`, `stream_map`, `try`, `lambda`, etc. |
| `scope` | enum | where to apply: `class_body`, `method_body`, `field`, `file` |
| `file_pattern` | glob | filename must match (e.g. `*Test.java`) |
| `exclude_path` | list[glob] | candidate dropped if path matches any glob |

**Composition rules:**
- Multiple hint keys are combined with **AND** — every specified hint must hold.
- Values within a list hint are combined with **OR** — any one match suffices.
- An empty `ast_hints` block means the pattern applies to every file in scope
  (used sparingly — defeats the pre-filter, raises token cost).

The hint set is intentionally closed. New hint types require a schema version bump
and a corresponding tree-sitter query translator, so pattern files remain portable
across CodeScope versions.

---

## Analysis Engine

### Token Budget & Chunking

`max_tokens_per_call` (default 6000) bounds the code context sent per LLM call.
Hot spot files frequently exceed this. The chunking strategy:

```
if file_tokens ≤ budget:
    send whole file

else:                                  # large hot spot file
    for each method matching the pattern group's ast_hints:
        chunk = class_context_summary
              + target method body
              + immediate callee bodies (if within remaining budget)
        emit chunk
```

The **class context summary** is a compact header — class name, annotations,
field declarations, and all method signatures — so the LLM understands the
method's surroundings without the full class body. A 2,000-line God class is
analysed as N method-level chunks, each carrying the same summary.

Patterns are grouped per chunk: one LLM call evaluates every pattern whose
`ast_hints` matched that chunk, rather than one call per pattern.

### Finding Deduplication & Aggregation

Findings arrive from multiple LLM calls — one per (chunk × pattern group).
Overlapping chunks can yield the same finding twice. Deduplication runs in
two stages.

**Stage 1 — instance dedup (within a file):**

```
dedup key = (pattern_id, file_path, overlapping_line_range)

two findings with the same pattern_id whose line ranges overlap
  → merged into one instance
  → higher severity wins; descriptions concatenated if materially different
```

**Stage 2 — pattern aggregation (across the codebase):**

```
group surviving instances by pattern_id
  → instance_count   = total instances
  → file_count       = distinct files
  → frequency        = instance_count   (primary sort key for the report)
```

The report is ordered by `frequency` descending. This is the deliberate core
behaviour: a smell appearing 11 times outranks a one-off critical finding,
because systematic patterns are what a reviewer most needs surfaced.

### False Positive Feedback Loop

When a reviewer marks a finding as a false positive in the Web UI, the
finding's code snippet and surrounding context are appended to the pattern's
`negative_examples`:

```yaml
- id: spring-sec-1
  name: Unnecessary User Lookup via Repository
  # ... existing fields ...
  negative_examples:
    - snippet: |
        userRepository.findById(adminTargetId)   # looking up a DIFFERENT user
      reason: admin operation, not the authenticated principal
```

On the next run, `negative_examples` are injected into the prompt as explicit
"do not flag cases resembling these" instructions. The pattern self-calibrates
from real review feedback rather than requiring the author to anticipate every
exception.

Each pattern also tracks a rolling false-positive rate across sessions.
Patterns exceeding a configurable threshold are surfaced on the Patterns page
for the reviewer to refine the `ast_hints` or `prompt_supplement`. A pattern
that is consistently wrong is a pattern that erodes trust — the tool makes
that visible rather than letting it quietly degrade every review.

---

## Pattern Library Distribution

Pattern libraries are plain YAML files in a Git repository. Git is the distribution
mechanism — no central registry, no package manager, just a URL and a ref.
This is intentional: organisations keep their patterns in their own infrastructure,
never touching a public registry.

### Configuration

```toml
[[pattern_libraries]]
name   = "builtin"
source = "builtin"                  # ships with codescope, always present

[[pattern_libraries]]
name   = "spring-community"
source = "https://github.com/codescope-community/spring-patterns"
ref    = "v1.2.0"                   # pinned tag — patterns don't shift under a review

[[pattern_libraries]]
name   = "myteam"
source = "https://gitlab.myorg.com/architecture/codescope-patterns"
ref    = "main"
auth   = "env:GITLAB_TOKEN"         # token from environment, not stored in config

[[pattern_libraries]]
name   = "local"
source = "~/.codescope/patterns"    # always checked last, local always wins on conflict
```

Libraries are resolved in declaration order. On conflict, later entries win.
`local` is always appended last by convention so local overrides are always respected.

### Library Types

| Type | Example | Purpose |
|---|---|---|
| Built-in | ships with codescope | Spring/Angular framework-semantic smells |
| Community | `github.com/codescope-community/spring-patterns` | Maintained, semver-tagged, PR-driven |
| Organisation | internal GitLab repo | Accumulated patterns from real reviews, private |
| Engagement | client repo | Patterns discovered during a specific engagement |
| Domain vertical | `telco-patterns`, `banking-compliance-patterns` | Industry-specific smells |

### Namespacing

Pattern IDs are prefixed with library name to prevent collision across sources:

```
builtin/spring-data-2
spring-community/trans-private-1
myteam/user-lookup-1
local/objectmapper-local-1
```

A local pattern with the same base ID as a community pattern overrides it.
Explicit override can also be declared in config:

```toml
[[pattern_overrides]]
override = "spring-community/trans-private-1"
with     = "myteam/trans-private-1"
```

### Library Manager

`~/.codescope/libraries/` holds cloned repos. Each library is a standard git clone.
`codescope patterns update` runs `git fetch` + `git checkout <ref>` for all sources.
Pinned libraries (exact tag or commit) are never auto-updated.

### Saving Patterns During a Review

When a reviewer creates a new pattern interactively, they choose a destination:

```
Pattern created: "Local ObjectMapper instantiation"

Save to:
  [1] local     (~/.codescope/patterns)        immediate, no push needed
  [2] myteam    (gitlab.myorg.com/…/patterns)  commits to local clone
  [3] new library…

Selection: 2

Committed to myteam — run 'codescope patterns push myteam' to share with your team.
```

Committing to a team library creates a git commit in the cloned repo.
`push` is a separate step — the reviewer may want to refine the pattern first.
This turns every review session into a potential contribution to shared knowledge.

### Consulting Use Case

A consultant arrives with their personal library built over years of reviews.
During an engagement they add client-specific patterns.
On completion they leave the client with their own library that persists independently.
The consultant's personal library retains nothing client-specific unless they
explicitly copy patterns across.

---

## Interactive Pattern Creation

The mechanism by which the library grows during a review session.

**Pattern creation flow:**

```
Reviewer notices something suspicious in a hot spot file
  │
  └─ presses [N] — "new pattern"
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  Describe the smell in plain language:       │
  │                                             │
  │  > ObjectMapper instantiated as a local     │
  │    variable inside a Spring service method  │
  │    instead of being injected as a bean      │
  │                                             │
  └──────────────────┬──────────────────────────┘
                     │  LLM generates draft YAML
                     ▼
  ┌─────────────────────────────────────────────┐
  │  Draft pattern — review and edit:           │
  │                                             │
  │  name: Local ObjectMapper Instantiation     │
  │  severity: medium                           │
  │  ast_hints:                                 │
  │    class_instantiation: ObjectMapper        │
  │    scope: method_body                       │
  │  fix_template: ...                          │
  │                                             │
  │  [E]dit  [V]alidate  [S]ave  [D]iscard      │
  └──────────────────┬──────────────────────────┘
                     │  [V]alidate pressed
                     ▼
  ┌─────────────────────────────────────────────┐
  │  Running pattern across full index...       │
  │                                             │
  │  ✓ Found 7 instances in 5 files             │
  │                                             │
  │  OrderService.java:114                      │
  │  PaymentService.java:67, :203               │
  │  NotificationService.java:88                │
  │  ReportService.java:41                      │
  │                                             │
  │  [S]ave to library  [D]iscard               │
  └─────────────────────────────────────────────┘
```

The "found N more instances" moment is the tool proving its value in real time.
It validates the pattern and hands the reviewer the full picture immediately.

---

## Web UI Screen Flow

```
┌──────────────────────────────────────────────────────────┐
│  localhost:8421  ·  CodeScope                            │
│  ──────────────────────────────────────────────────────  │
│  Hot Spots   Review   Patterns   Report                  │
└──────────────────────────────────────────────────────────┘

HOT SPOTS PAGE
┌─────────────────────────────────────────────────────┐
│  my-service  ·  134 files indexed  ·  top 20 shown  │
│                                                     │
│  #  File                     Score  F  C  S  D      │
│  ─────────────────────────────────────────────────  │
│  1  OrderService.java          94   ██ ██ █  ██     │
│  2  UserController.java        87   ██ █  █  ██     │
│  3  PaymentProcessor.java      81   █  ██ ██ █      │
│  ...                                                │
│                                                     │
│  Signals: [F]req  [C]omplexity  [S]ize  [D]eps      │
│                                          [Review →] │
└─────────────────────────────────────────────────────┘

REVIEW PAGE  (code left · findings right)
┌──────────────────────────┬──────────────────────────┐
│  OrderService.java       │  Findings  ·  3 patterns  │
│  ──────────────────────  │  ───────────────────────  │
│  114  List<Order> map(   │  ● Query in stream  ×4   │
│  115    items.stream()   │    findById in map body   │
│  116 ►  .map(i ->        │    → use findAllById()    │
│  117      repo.find(     │                           │
│  118        i.getId()))  │  ● Missing readOnly  ×2   │
│  119    .toList();       │    → add readOnly=true    │
│                          │                           │
│  ──────────────────────  │  ● God class (1)          │
│  Changed 47× · CC: 14   │    18 dependencies        │
│  18 dependencies         │    → split responsibilities│
│                          │                           │
│                          │  [+ New pattern]          │
│  [← prev]  [next →]      │  [→ Report]               │
└──────────────────────────┴──────────────────────────┘

REPORT PAGE
┌─────────────────────────────────────────────────────┐
│  Review Report  ·  my-service                       │
│                                                     │
│  SYSTEMATIC FINDINGS                                │
│  1. Query inside stream mapping      11 instances   │
│     7 files  ·  medium                              │
│  2. Unnecessary user DB lookup        9 instances   │
│     7 controllers  ·  medium                        │
│  3. @Transactional missing readOnly   6 instances   │
│                                                     │
│  [↓ Markdown]  [↓ HTML]  [→ GitLab issues]         │
└─────────────────────────────────────────────────────┘
```

---

## Pattern Library — Built-in Categories

The built-in library focuses on the smells that static analysis fundamentally
cannot detect: those requiring runtime framework knowledge.

**Java / Spring Boot**

| File | Focus |
|---|---|
| `java_spring_context.yaml` | `@Transactional` on private/same-class call; `@Async` proxy bypass; `@Scheduled` swallowing exceptions |
| `java_spring_data.yaml` | Query in loop; N+1 on stream mapping; `FetchType.EAGER` on collections; missing `readOnly=true` |
| `java_spring_security.yaml` | Redundant user lookup; direct `SecurityContextHolder` access in service layer; BCrypt strength |
| `java_architecture.yaml` | Layer violations; anemic domain model; God service; constructor over-injection |
| `java_testing.yaml` | `@SpringBootTest` for unit-scope tests; missing `@DirtiesContext` on state mutation; `@MockBean` in full context test |

**Angular / TypeScript**

| File | Focus |
|---|---|
| `angular_rxjs.yaml` | Subscription leaks; manual subscribe where async pipe fits; Subject exposure; nested subscribes |
| `angular_lifecycle.yaml` | `ChangeDetectorRef.detectChanges()` in `ngAfterViewInit`; `Router.navigate()` in constructor; `translate.instant()` before load |
| `angular_architecture.yaml` | Smart/dumb violation; missing OnPush; feature module isolation; state management boundary |
| `angular_testing.yaml` | `detectChanges()` before inputs set; missing `async` in guards; `fakeAsync` misuse |

---

## Review Report Structure

The primary output is a structured review document, not a flat issue list.

```markdown
# Codebase Review: my-service
Generated: 2026-05-25  ·  Reviewer: —  ·  Hot spots analysed: 20 of 134 files

## Executive Summary
3 systematic issues found across 20 high-risk files.
Most critical: query-in-loop pattern present in 7 service classes,
likely introduced from a common template. Estimated fix effort: 2 days.

## Systematic Findings

### 1. Query Inside Stream Mapping  ·  11 instances  ·  7 files  ·  medium
**Pattern:** java_spring_data / spring-data-2
**Impact:** N+1 queries on every invocation. At current data volumes,
each affected endpoint fires 50–400 additional DB queries per request.

**Instances:**
- `OrderService.java:114` — productRepository.findById inside order line map
- `PaymentService.java:67` — userRepository.findById inside payment item stream
- ... (9 more)

**Suggested fix:**
Replace per-item repository calls with a single bulk query outside the stream:
  List<Long> ids = items.stream().map(Item::getProductId).toList();
  Map<Long, Product> products = productRepository.findAllById(ids)
      .stream().collect(Collectors.toMap(Product::getId, p -> p));

### 2. Unnecessary User Lookup  ·  9 instances  ·  7 controllers  ·  medium
...

## Hot Spot Analysis
| Rank | File | Score | Change Freq | Complexity | Dependencies |
...

## Pattern Library Used
12 built-in patterns  ·  2 session patterns (new this review)
```

---

## LLM Provider Configuration

```toml
[llm]
base_url = "http://localhost:8080/v1"
model    = "qwen3-30b-a3b"
api_key  = "sk-local"
timeout  = 120

[llm.profiles.openai]
base_url = "https://api.openai.com/v1"
model    = "gpt-4o"
api_key  = "sk-..."

[review]
top_n_hotspots   = 20
hotspot_weights  = { change_frequency = 1.0, complexity = 0.8, dependencies = 0.6, recency = 0.4 }
max_tokens_per_call = 6000

[server]
port = 8421
open_browser = true               # auto-open on codescope review

[index]
path          = ".codescope/index"
languages     = ["java", "typescript"]
exclude_globs = ["**/generated/**", "**/target/**", "**/node_modules/**"]
incremental   = true

[output]
default_format = "markdown"

# Pattern libraries — resolved in order, later wins on conflict
[[pattern_libraries]]
name   = "builtin"
source = "builtin"

[[pattern_libraries]]
name   = "spring-community"
source = "https://github.com/codescope-community/spring-patterns"
ref    = "v1.2.0"

[[pattern_libraries]]
name   = "myteam"
source = "https://gitlab.myorg.com/architecture/codescope-patterns"
ref    = "main"
auth   = "env:GITLAB_TOKEN"

[[pattern_libraries]]
name   = "local"
source = "~/.codescope/patterns"
```

---

## CLI

```bash
# First-time setup
codescope init

# Index project (run from project root)
codescope index [--incremental]

# Start a review session (opens browser)
codescope review

# Headless review — top hot spots, all patterns, markdown report
codescope review --no-server --output report.md

# Scope to specific concern
codescope review --tags spring-security,spring-data
codescope review --top 10                  # review top 10 hot spots only
codescope review --profile openai          # use named LLM profile

# Pattern management
codescope patterns list [--tag spring] [--library myteam]
codescope patterns show spring-community/trans-private-1
codescope patterns edit myteam/user-lookup-1
codescope patterns new                     # interactive LLM-assisted creation

# Pattern library management
codescope patterns add <git-url> [--name <name>] [--ref <tag-or-commit>]
codescope patterns update [<library-name>] # fetch latest for unpinned libraries
codescope patterns push <library-name>     # push local commits to remote
codescope patterns libraries               # list configured libraries + sync status

# Export last session in a different format
codescope export --format html
codescope export --format gitlab
```

---

## Key Design Decisions

**Web UI with local Python server.**
The review workflow requires reading code alongside findings. A terminal interface
cannot provide side-by-side code view, inline annotations, or the Monaco editor
needed for comfortable pattern creation. FastAPI serves the analysis backend;
React runs in the browser. The same backend drives CLI headless mode for CI and
can be packaged as a desktop app (PyWebView/Tauri) without changing the architecture.

**Git as the pattern distribution mechanism.**
Pattern libraries are YAML files in Git repositories. No central registry, no package
manager — just a URL and a ref. Organisations keep their patterns in their own
infrastructure. Community libraries are PR-driven and semver-tagged. The model is
Homebrew taps, not npm. For regulated environments this is a feature: nothing
leaves the network perimeter unless explicitly pushed.

**Pattern namespacing prevents library conflicts.**
IDs are prefixed with library name (`spring-community/trans-private-1`). Local
library always wins. Explicit overrides available in config. A team can fork a
community pattern, override it locally, and contribute the fix back via PR.


Analysing every file with an LLM is slow and expensive. Hot spot ranking
focuses attention on the 10–20% of files where 80% of real problems live.
This is not a heuristic guess — it is backed by change frequency data
from the actual repo history.

**Framework-semantic smells, not syntax smells.**
The built-in library targets smells that require knowing what Spring or Angular
does at runtime. These are undetectable by any rule-based static analyzer.
The LLM's training on vast codebases gives it this semantic layer.

**70–80% accuracy is the right target.**
This is a reviewer aid, not a CI gate. A false positive costs 30 seconds
to dismiss. A missed pattern that appears 11 times costs a day of reading.
The tool optimises for recall over precision.

**The pattern library is the compounding asset.**
The LLM is interchangeable. The pattern library — built-in smells plus
patterns added during real reviews — encodes hard-won architectural knowledge
in a form that is shareable, version-controllable, and grows with every engagement.

**Interactive pattern creation closes the loop.**
The moment a reviewer describes a new smell and sees "found 8 more instances"
is the core value proposition of the tool. It turns a manual observation into
a reusable, codebase-wide finding in under a minute.

**Review report, not issue list.**
The output is a structured document a reviewer hands to a team lead.
Systematic findings ranked by frequency, each with instances and a concrete
fix. Not 47 individual tickets.

---

## Out of Scope for v1

- Automatic fix application
- IDE plugins
- Multi-repo / monorepo federation
- Continuous / watch-mode analysis
- Windows native (WSL2)
- Fine-tuned models
