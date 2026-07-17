from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class SearchTier(BaseModel):
    name: str
    stars: str
    active_days: int = Field(gt=0)


class CategoryRule(BaseModel):
    name: str
    threshold: int = 3
    topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    schema_version: int = 1
    repository: str
    scan_limit: int = Field(gt=0, le=1000)
    file_size_limit: int = Field(gt=0)
    history_days: int = Field(default=30, gt=7)
    readme_file_limit: int = Field(default=6, gt=0)
    search_tiers: list[SearchTier]
    categories: list[CategoryRule]

def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    if not isinstance(value, dict):
        raise ValueError(f"expected a mapping in {path}")
    return value


def load_settings(root: Path) -> Settings:
    return Settings.model_validate(_read_yaml(root / "config.yml"))


def load_overrides(root: Path) -> dict[str, str]:
    value = _read_yaml(root / "config" / "category-overrides.yml")
    overrides = value.get("overrides", {})
    if not isinstance(overrides, dict):
        raise ValueError("category overrides must be a mapping")
    return {str(key).lower(): str(category) for key, category in overrides.items()}
