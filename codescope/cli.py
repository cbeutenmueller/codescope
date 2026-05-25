from __future__ import annotations
import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import track

app = typer.Typer(
    name="codescope",
    help="Code review companion — finds framework-semantic smells.",
    no_args_is_help=True,
)
patterns_app = typer.Typer(help="Pattern library management.")
app.add_typer(patterns_app, name="patterns")

console = Console()


def _find_root() -> Path:
    """Walk up from cwd to find a project root (git repo or .codescope dir)."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists() or (parent / ".codescope").exists():
            return parent
    return cwd


def _load_cfg(root: Path):
    from codescope.config import load_config

    return load_config(root)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


@app.command()
def init(
    directory: Path = typer.Argument(None, help="Project directory (default: current directory)"),
) -> None:
    """Initialise CodeScope in the current project."""
    root = directory or Path.cwd()
    codescope_dir = root / ".codescope"
    codescope_dir.mkdir(parents=True, exist_ok=True)

    config_path = codescope_dir / "config.toml"
    if not config_path.exists():
        config_path.write_text(_DEFAULT_CONFIG_TOML, encoding="utf-8")
        console.print(f"[green]✓[/green] Created {config_path}")
    else:
        console.print(f"[yellow]→[/yellow] Config already exists: {config_path}")

    user_dir = Path.home() / ".codescope"
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "patterns").mkdir(exist_ok=True)

    console.print(
        "[green]✓[/green] CodeScope initialised. Edit .codescope/config.toml to configure your LLM."
    )


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------


@app.command()
def index(
    directory: Path = typer.Argument(None, help="Project root (default: auto-detected)"),
    full: bool = typer.Option(False, "--full", help="Force full re-index"),
) -> None:
    """Build the structural index for the project."""
    root = directory or _find_root()
    from codescope.config import load_config

    config = load_config(root)
    if full:
        config.index.incremental = False

    from codescope.indexer.incremental import build_index
    from codescope.indexer.walker import walk_files

    languages = set(config.index.languages)
    files = walk_files(root, config.index.exclude_globs, languages)
    console.print(f"Found [bold]{len(files)}[/bold] source files in [cyan]{root}[/cyan]")

    with console.status("Indexing…"):
        idx = build_index(root, config)

    db = root / config.index.path / "codescope.db"
    console.print(f"[green]✓[/green] Index written to {db}")


# ---------------------------------------------------------------------------
# review
# ---------------------------------------------------------------------------


@app.command()
def review(
    directory: Path = typer.Argument(None, help="Project root (default: auto-detected)"),
    output: Path = typer.Option(None, "--output", "-o", help="Write report to file"),
    fmt: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown"),
    tags: str = typer.Option(
        None, "--tags", help="Comma-separated pattern tags to scope the review"
    ),
    top: int = typer.Option(None, "--top", help="Override top-N hot spots"),
    profile: str = typer.Option(None, "--profile", help="LLM profile name from config"),
    no_server: bool = typer.Option(False, "--no-server", help="Headless mode — no browser"),
) -> None:
    """Run a code review session."""
    root = directory or _find_root()
    config = _load_cfg(root)

    if top is not None:
        config.review.top_n_hotspots = top

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    from codescope.analysis.runner import AnalysisRunner
    from codescope.output.markdown import MarkdownReporter

    runner = AnalysisRunner(config, root, llm_profile=profile)

    findings_seen = 0

    def progress_cb(stage: str, *args):
        nonlocal findings_seen
        if stage == "ranking":
            console.print(f"Ranking {args[0]} files…")
        elif stage == "analysing":
            i, total, path = args
            rel = str(Path(path).relative_to(root)) if Path(path).is_relative_to(root) else path
            console.print(f"  [{i}/{total}] {rel}")

    with console.status("Running analysis…"):
        session = asyncio.run(runner.run(tags=tag_list, progress_cb=progress_cb))

    total_instances = sum(af.instance_count for af in session.aggregated_findings)
    console.print(
        f"\n[bold]Review complete.[/bold] "
        f"{len(session.aggregated_findings)} pattern(s), "
        f"{total_instances} instance(s) across "
        f"{len(session.hotspot_paths)} hot spot(s)."
    )

    if session.aggregated_findings:
        _print_findings_table(session)

    if output:
        reporter = MarkdownReporter()
        reporter.write(session, output)
    else:
        session_path = session.save()
        console.print(f"Session saved: {session_path}")
        console.print(
            "\nRe-export with: [cyan]codescope export --session {session.session_id}[/cyan]"
        )


def _print_findings_table(session) -> None:
    table = Table(title="Systematic Findings", show_lines=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Pattern", style="cyan")
    table.add_column("Instances", justify="right")
    table.add_column("Files", justify="right")
    table.add_column("Severity", style="yellow")

    for i, af in enumerate(session.aggregated_findings, 1):
        table.add_row(
            str(i),
            af.pattern_name,
            str(af.instance_count),
            str(af.file_count),
            af.severity.value,
        )
    console.print(table)


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


@app.command()
def export(
    session_id: str = typer.Option(None, "--session", help="Session ID to export"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file"),
    fmt: str = typer.Option("markdown", "--format", "-f", help="Output format"),
) -> None:
    """Re-export a saved review session as a report."""
    from codescope.analysis.session import ReviewSession
    from codescope.output.markdown import MarkdownReporter

    if session_id is None:
        # Find the most recent session
        sessions_dir = Path.home() / ".codescope" / "sessions"
        sessions = sorted(
            sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not sessions:
            console.print("[red]No saved sessions found.[/red]")
            raise typer.Exit(1)
        session_id = sessions[0].stem
        console.print(f"Using most recent session: [cyan]{session_id}[/cyan]")

    session = ReviewSession.load(session_id)

    reporter = MarkdownReporter()
    report = reporter.render(session)

    if output:
        output.write_text(report, encoding="utf-8")
        console.print(f"[green]✓[/green] Report written to {output}")
    else:
        console.print(report)


# ---------------------------------------------------------------------------
# patterns subcommands
# ---------------------------------------------------------------------------


@patterns_app.command("list")
def patterns_list(
    tag: str = typer.Option(None, "--tag", help="Filter by tag"),
    library: str = typer.Option(None, "--library", help="Filter by library"),
) -> None:
    """List available patterns."""
    root = _find_root()
    config = _load_cfg(root)

    from codescope.patterns.loader import load_patterns

    patterns = load_patterns(config)

    if tag:
        patterns = [p for p in patterns if tag in p.tags]
    if library:
        patterns = [p for p in patterns if p.library == library]

    table = Table(title=f"Patterns ({len(patterns)})", show_lines=False)
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Language", style="dim")
    table.add_column("Severity", style="yellow")
    table.add_column("Tags", style="dim")

    for p in sorted(patterns, key=lambda x: x.namespaced_id):
        table.add_row(
            p.namespaced_id,
            p.name,
            p.language,
            p.severity,
            ", ".join(p.tags),
        )
    console.print(table)


@patterns_app.command("show")
def patterns_show(
    pattern_id: str = typer.Argument(..., help="Pattern ID (e.g. builtin/spring-data-1)"),
) -> None:
    """Show full details of a pattern."""
    root = _find_root()
    config = _load_cfg(root)

    from codescope.patterns.loader import load_patterns

    patterns = {p.namespaced_id: p for p in load_patterns(config)}

    p = patterns.get(pattern_id)
    if p is None:
        console.print(f"[red]Pattern not found:[/red] {pattern_id}")
        raise typer.Exit(1)

    console.print(f"[bold]{p.namespaced_id}[/bold] — {p.name}")
    console.print(f"Language: {p.language}  Severity: {p.severity}  Category: {p.category}")
    console.print(f"\n{p.description.strip()}")
    if p.prompt_supplement:
        console.print(f"\n[dim]Guidance:[/dim] {p.prompt_supplement.strip()}")
    if p.fix_template:
        console.print(f"\n[dim]Fix:[/dim]\n{p.fix_template.strip()}")
    console.print(f"\nTags: {', '.join(p.tags)}")


# ---------------------------------------------------------------------------
# Config template
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG_TOML = """\
[llm]
base_url = "https://api.openai.com/v1"
model    = "gpt-4o-mini"
api_key  = "sk-YOUR-KEY-HERE"
timeout  = 120

[review]
top_n_hotspots  = 20
max_tokens_per_call = 6000

[review.hotspot_weights]
change_frequency = 1.0
complexity       = 0.8
dependencies     = 0.6
recency          = 0.4

[server]
port         = 8421
open_browser = true

[index]
path          = ".codescope/index"
languages     = ["java", "typescript"]
exclude_globs = ["**/generated/**", "**/target/**", "**/node_modules/**", "**/dist/**"]
incremental   = true

[output]
default_format = "markdown"

[[pattern_libraries]]
name   = "builtin"
source = "builtin"

[[pattern_libraries]]
name   = "local"
source = "~/.codescope/patterns"
"""


if __name__ == "__main__":
    app()
