from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class AstHints(BaseModel):
    """Structural pre-filter applied before LLM analysis.

    Keys are AND-combined; list values within a key are OR-combined.
    An empty AstHints block means the pattern applies to every file in scope.
    """

    node_type: str | None = None
    annotations_present: list[str] = Field(default_factory=list)
    annotations_absent: list[str] = Field(default_factory=list)
    method_call_pattern: list[str] = Field(default_factory=list)
    parameter_type_present: list[str] = Field(default_factory=list)
    parameter_type_absent: list[str] = Field(default_factory=list)
    class_instantiation: list[str] = Field(default_factory=list)
    min_param_count: int | None = None
    max_param_count: int | None = None
    contains_construct: list[str] = Field(default_factory=list)
    scope: Literal["class_body", "method_body", "field", "file"] | None = None
    file_pattern: str | None = None
    exclude_path: list[str] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return not any(
            [
                self.node_type,
                self.annotations_present,
                self.annotations_absent,
                self.method_call_pattern,
                self.parameter_type_present,
                self.parameter_type_absent,
                self.class_instantiation,
                self.min_param_count is not None,
                self.max_param_count is not None,
                self.contains_construct,
                self.scope,
                self.file_pattern,
                self.exclude_path,
            ]
        )


class NegativeExample(BaseModel):
    snippet: str
    reason: str


class Pattern(BaseModel):
    id: str
    name: str
    category: str
    language: Literal["java", "typescript", "any"] = "any"
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    description: str
    ast_hints: AstHints = Field(default_factory=AstHints)
    prompt_supplement: str = ""
    fix_template: str = ""
    negative_examples: list[NegativeExample] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    enabled: bool = True

    # Set by the loader after namespacing
    library: str = ""

    @property
    def namespaced_id(self) -> str:
        if self.library and not self.id.startswith(f"{self.library}/"):
            return f"{self.library}/{self.id}"
        return self.id
