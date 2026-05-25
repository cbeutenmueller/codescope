from __future__ import annotations
import tomllib
from pathlib import Path
from pydantic import BaseModel, Field


class HotspotWeights(BaseModel):
    change_frequency: float = 1.0
    complexity: float = 0.8
    dependencies: float = 0.6
    recency: float = 0.4


class ReviewConfig(BaseModel):
    top_n_hotspots: int = 20
    hotspot_weights: HotspotWeights = Field(default_factory=HotspotWeights)
    max_tokens_per_call: int = 6000


class LLMProfile(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key: str = "sk-placeholder"
    timeout: int = 120


class LLMConfig(LLMProfile):
    profiles: dict[str, LLMProfile] = Field(default_factory=dict)


class ServerConfig(BaseModel):
    port: int = 8421
    open_browser: bool = True


class IndexConfig(BaseModel):
    path: str = ".codescope/index"
    languages: list[str] = Field(default_factory=lambda: ["java", "typescript"])
    exclude_globs: list[str] = Field(
        default_factory=lambda: [
            "**/generated/**",
            "**/target/**",
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/.git/**",
        ]
    )
    incremental: bool = True


class OutputConfig(BaseModel):
    default_format: str = "markdown"


class PatternLibraryConfig(BaseModel):
    name: str
    source: str
    ref: str = "main"
    auth: str | None = None


class PatternOverrideConfig(BaseModel):
    override: str
    with_: str = Field(alias="with")


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    index: IndexConfig = Field(default_factory=IndexConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    pattern_libraries: list[PatternLibraryConfig] = Field(
        default_factory=lambda: [
            PatternLibraryConfig(name="builtin", source="builtin"),
            PatternLibraryConfig(name="local", source="~/.codescope/patterns"),
        ]
    )
    pattern_overrides: list[PatternOverrideConfig] = Field(default_factory=list)

    def llm_profile(self, name: str | None) -> LLMProfile:
        if name and name in self.llm.profiles:
            return self.llm.profiles[name]
        return self.llm


def load_config(project_root: Path | None = None) -> AppConfig:
    raw: dict = {}

    user_cfg = Path.home() / ".codescope" / "config.toml"
    if user_cfg.exists():
        with open(user_cfg, "rb") as f:
            raw = _deep_merge(raw, tomllib.load(f))

    if project_root is not None:
        proj_cfg = project_root / ".codescope" / "config.toml"
        if proj_cfg.exists():
            with open(proj_cfg, "rb") as f:
                raw = _deep_merge(raw, tomllib.load(f))

    return AppConfig.model_validate(raw)


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
