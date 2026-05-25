from __future__ import annotations
import asyncio
import uuid
from pathlib import Path

from codescope.config import AppConfig
from codescope.hotspot.ranker import rank_files
from codescope.hotspot.scorer import HotspotScore
from codescope.indexer.walker import walk_files
from codescope.indexer.ast_extractor import AstExtractor
from codescope.patterns.loader import load_patterns
from codescope.patterns.schema import Pattern
from codescope.llm.provider import LLMProvider
from codescope.llm.prompt_builder import build_analysis_prompt
from codescope.llm.response_parser import parse_findings
from codescope.analysis.finding import Finding
from codescope.analysis.aggregator import aggregate
from codescope.analysis.session import ReviewSession


class AnalysisRunner:
    def __init__(
        self, config: AppConfig, project_root: Path, llm_profile: str | None = None
    ) -> None:
        self._config = config
        self._root = project_root
        self._llm = LLMProvider(config.llm_profile(llm_profile))
        self._extractor = AstExtractor()

    async def run(
        self,
        tags: list[str] | None = None,
        progress_cb=None,
    ) -> ReviewSession:
        patterns = load_patterns(self._config)
        if tags:
            patterns = [p for p in patterns if any(t in p.tags for t in tags)]

        languages = set(self._config.index.languages)
        file_paths = walk_files(self._root, self._config.index.exclude_globs, languages)

        if progress_cb:
            progress_cb("ranking", len(file_paths))

        hotspots = rank_files(file_paths, self._root, self._config)

        all_findings: list[Finding] = []
        for i, hs in enumerate(hotspots):
            if progress_cb:
                progress_cb("analysing", i + 1, len(hotspots), hs.path)
            findings = await self._analyse_file(hs, patterns)
            all_findings.extend(findings)

        aggregated = aggregate(
            all_findings,
            fix_map={p.namespaced_id: p.fix_template for p in patterns},
        )

        session = ReviewSession(
            session_id=str(uuid.uuid4())[:8],
            project_root=str(self._root),
            hotspot_paths=[hs.path for hs in hotspots],
            aggregated_findings=aggregated,
            patterns_used=[p.namespaced_id for p in patterns],
        )
        return session

    async def _analyse_file(
        self,
        hs: HotspotScore,
        patterns: list[Pattern],
    ) -> list[Finding]:
        try:
            text = Path(hs.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        # Determine which patterns are candidates for this file
        candidates = self._filter_candidates(hs.path, text, patterns)
        if not candidates:
            return []

        max_tokens = self._config.review.max_tokens_per_call
        chunks = self._chunk_file(text, max_tokens)

        pattern_name_map = {p.namespaced_id: p.name for p in candidates}
        findings: list[Finding] = []

        for chunk_text, line_offset in chunks:
            messages = build_analysis_prompt(hs.path, chunk_text, candidates)
            try:
                response = await self._llm.complete_json(messages, max_tokens=1500)
                chunk_findings = parse_findings(response, hs.path, pattern_name_map)
                # Adjust line numbers for chunks that started mid-file
                for f in chunk_findings:
                    f.location.line_start += line_offset
                    f.location.line_end += line_offset
                findings.extend(chunk_findings)
            except Exception:
                pass

        return findings

    def _filter_candidates(
        self,
        file_path: str,
        text: str,
        patterns: list[Pattern],
    ) -> list[Pattern]:
        """Apply AST hints as a quick pre-filter before calling the LLM."""
        candidates = []
        for pattern in patterns:
            if self._hint_matches(file_path, text, pattern):
                candidates.append(pattern)
        return candidates

    def _hint_matches(self, file_path: str, text: str, pattern: Pattern) -> bool:
        hints = pattern.ast_hints
        if hints.is_empty():
            return True

        fp = file_path.lower()

        # Language filter
        if pattern.language != "any":
            ext_map = {"java": ".java", "typescript": (".ts", ".tsx")}
            expected = ext_map.get(pattern.language, "")
            if isinstance(expected, str):
                if not fp.endswith(expected):
                    return False
            elif not fp.endswith(expected):
                return False

        # file_pattern
        if hints.file_pattern:
            import fnmatch

            if not fnmatch.fnmatch(Path(file_path).name, hints.file_pattern):
                return False

        # exclude_path
        if hints.exclude_path:
            import fnmatch

            for excl in hints.exclude_path:
                if fnmatch.fnmatch(file_path, excl):
                    return False

        # annotations_present (any must be present)
        if hints.annotations_present:
            if not any(ann in text for ann in hints.annotations_present):
                return False

        # annotations_absent (none must be present)
        if hints.annotations_absent:
            if any(ann in text for ann in hints.annotations_absent):
                return False

        # method_call_pattern (any glob must match somewhere in text)
        if hints.method_call_pattern:
            import fnmatch

            if not any(
                any(fnmatch.fnmatch(token, pat) for token in text.split())
                for pat in hints.method_call_pattern
            ):
                # Fall back to substring check for patterns without wildcards
                if not any(pat.replace("*", "") in text for pat in hints.method_call_pattern):
                    return False

        # class_instantiation
        if hints.class_instantiation:
            if not any(f"new {cls}" in text for cls in hints.class_instantiation):
                return False

        return True

    def _chunk_file(self, text: str, max_tokens: int) -> list[tuple[str, int]]:
        """Split text into chunks. Rough estimate: 1 token ≈ 4 chars."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return [(text, 0)]

        lines = text.splitlines()
        chunks: list[tuple[str, int]] = []
        chunk_lines: list[str] = []
        chunk_start = 0
        char_count = 0

        for i, line in enumerate(lines):
            chunk_lines.append(line)
            char_count += len(line) + 1
            if char_count >= max_chars:
                chunks.append(("\n".join(chunk_lines), chunk_start))
                chunk_lines = []
                chunk_start = i + 1
                char_count = 0

        if chunk_lines:
            chunks.append(("\n".join(chunk_lines), chunk_start))

        return chunks
