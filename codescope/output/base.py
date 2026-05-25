from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from codescope.analysis.session import ReviewSession


class BaseReporter(ABC):
    @abstractmethod
    def render(self, session: ReviewSession) -> str: ...

    def write(self, session: ReviewSession, output_path: Path) -> None:
        content = self.render(session)
        output_path.write_text(content, encoding="utf-8")
        print(f"Report written to {output_path}")
