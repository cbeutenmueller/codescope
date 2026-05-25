from __future__ import annotations
import asyncio
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

from codescope.config import load_config, AppConfig
from codescope.analysis.session import ReviewSession

app = FastAPI(title="CodeScope", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: session_id → (session | None, events queue)
_sessions: dict[str, ReviewSession | None] = {}
_queues: dict[str, asyncio.Queue] = {}
_config: AppConfig | None = None
_project_root: Path | None = None


def configure(project_root: Path, config: AppConfig) -> None:
    global _config, _project_root
    _project_root = project_root
    _config = config


def preload_session(session: "ReviewSession") -> None:
    """Inject a completed session so the server can serve it immediately."""
    _sessions[session.session_id] = session


# ---------------------------------------------------------------------------
# Serve React frontend (built to server/static/)
# ---------------------------------------------------------------------------

_STATIC_DIR = Path(__file__).parent / "static"
if _STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(_STATIC_DIR / "assets")), name="assets")


@app.get("/", include_in_schema=False)
async def root():
    index = _STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return PlainTextResponse("CodeScope API — frontend not built yet. See /docs.")


# ---------------------------------------------------------------------------
# Review routes
# ---------------------------------------------------------------------------


@app.post("/api/review/start")
async def start_review(background_tasks: BackgroundTasks, tags: str = "", top: int | None = None):
    if _config is None or _project_root is None:
        raise HTTPException(503, "Server not configured")

    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = None
    _queues[session_id] = asyncio.Queue()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    background_tasks.add_task(_run_analysis, session_id, tag_list, top)
    return {"session_id": session_id, "status": "started"}


async def _run_analysis(session_id: str, tags: list[str] | None, top: int | None) -> None:
    from codescope.analysis.runner import AnalysisRunner

    q = _queues[session_id]
    config = _config.model_copy(deep=True)
    if top is not None:
        config.review.top_n_hotspots = top

    runner = AnalysisRunner(config, _project_root)

    def progress_cb(stage: str, *args):
        if stage == "ranking":
            q.put_nowait({"type": "progress", "stage": "ranking", "file_count": args[0]})
        elif stage == "analysing":
            i, total, path = args
            q.put_nowait(
                {
                    "type": "progress",
                    "stage": "analysing",
                    "current": i,
                    "total": total,
                    "file": path,
                }
            )

    try:
        session = await runner.run(tags=tags, progress_cb=progress_cb)
        _sessions[session_id] = session
        q.put_nowait({"type": "complete", "session_id": session_id})
    except Exception as exc:
        q.put_nowait({"type": "error", "message": str(exc)})


@app.get("/api/review/{session_id}")
async def get_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(404, "Session not found")
    session = _sessions[session_id]
    if session is None:
        return {"status": "running"}
    return _serialise_session(session)


@app.get("/api/review/{session_id}/hotspots")
async def get_hotspots(session_id: str):
    session = _get_session_or_404(session_id)
    return {"hotspots": session.hotspot_paths}


@app.get("/api/review/{session_id}/findings")
async def get_findings(session_id: str):
    session = _get_session_or_404(session_id)
    return (
        {
            "findings": [
                {
                    "pattern_id": af.pattern_id,
                    "pattern_name": af.pattern_name,
                    "severity": af.severity.value,
                    "instance_count": af.instance_count,
                    "file_count": af.file_count,
                    "fix_suggestion": af.fix_suggestion,
                    "instances": [
                        {
                            "file_path": f.location.file_path,
                            "line_start": f.location.line_start,
                            "line_end": f.location.line_end,
                            "description": f.description,
                        }
                        for f in af.instances
                    ],
                }
                for af in af_list
            ]
        }
        if (af_list := session.aggregated_findings) is not None
        else {"findings": []}
    )


# ---------------------------------------------------------------------------
# Pattern routes
# ---------------------------------------------------------------------------


@app.get("/api/patterns")
async def list_patterns(tag: str = "", library: str = ""):
    if _config is None:
        raise HTTPException(503, "Server not configured")
    from codescope.patterns.loader import load_patterns

    patterns = load_patterns(_config)
    if tag:
        patterns = [p for p in patterns if tag in p.tags]
    if library:
        patterns = [p for p in patterns if p.library == library]
    return {
        "patterns": [
            {
                "id": p.namespaced_id,
                "name": p.name,
                "category": p.category,
                "language": p.language,
                "severity": p.severity,
                "description": p.description,
                "tags": p.tags,
                "library": p.library,
            }
            for p in patterns
        ]
    }


@app.get("/api/patterns/{pattern_id:path}")
async def get_pattern(pattern_id: str):
    if _config is None:
        raise HTTPException(503, "Server not configured")
    from codescope.patterns.loader import load_patterns

    patterns = {p.namespaced_id: p for p in load_patterns(_config)}
    p = patterns.get(pattern_id)
    if p is None:
        raise HTTPException(404, f"Pattern not found: {pattern_id}")
    return {
        "id": p.namespaced_id,
        "name": p.name,
        "category": p.category,
        "language": p.language,
        "severity": p.severity,
        "description": p.description,
        "ast_hints": p.ast_hints.model_dump(exclude_none=True),
        "prompt_supplement": p.prompt_supplement,
        "fix_template": p.fix_template,
        "tags": p.tags,
        "negative_examples": [e.model_dump() for e in p.negative_examples],
    }


# ---------------------------------------------------------------------------
# Export routes
# ---------------------------------------------------------------------------


@app.get("/api/export/{session_id}/markdown")
async def export_markdown(session_id: str):
    session = _get_session_or_404(session_id)
    from codescope.output.markdown import MarkdownReporter

    report = MarkdownReporter().render(session)
    return PlainTextResponse(report, media_type="text/markdown")


# ---------------------------------------------------------------------------
# WebSocket — streams analysis events to the browser
# ---------------------------------------------------------------------------


@app.websocket("/ws/review/{session_id}")
async def review_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in _queues:
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return

    q = _queues[session_id]
    try:
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=30.0)
                await websocket.send_json(event)
                if event["type"] in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_session_or_404(session_id: str) -> ReviewSession:
    if session_id not in _sessions:
        raise HTTPException(404, "Session not found")
    session = _sessions[session_id]
    if session is None:
        raise HTTPException(409, "Session still running")
    return session


def _serialise_session(session: ReviewSession) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "project_root": session.project_root,
        "started_at": session.started_at,
        "status": "complete",
        "hotspot_count": len(session.hotspot_paths),
        "finding_count": sum(af.instance_count for af in session.aggregated_findings),
        "pattern_count": len(session.aggregated_findings),
        "patterns_used": len(session.patterns_used),
    }
