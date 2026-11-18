"""Load and validate the local YAML configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ConfigurationError(ValueError):
    """Raised when the local application configuration is missing or invalid."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class PathsConfig(StrictModel):
    victoriya_root: Path

    @field_validator("victoriya_root", mode="before")
    @classmethod
    def expand_root(cls, value: Any) -> Path:
        if not isinstance(value, (str, Path)):
            raise ValueError("paths.victoriya_root must be a path string")
        expanded = Path(os.path.expandvars(str(value))).expanduser()
        if not expanded.is_absolute():
            raise ValueError("paths.victoriya_root must be an absolute path")
        return expanded


class PhotoConfig(StrictModel):
    main_width: int = Field(default=600, gt=0, le=4000)
    main_height: int = Field(default=800, gt=0, le=4000)
    secondary_max_bytes: int = Field(default=2_500_000, gt=0)
    secondary_format: str = "jpg"

    @field_validator("secondary_format")
    @classmethod
    def supported_secondary_format(cls, value: str) -> str:
        normalized = value.lower().lstrip(".")
        if normalized != "jpg":
            raise ValueError("MVP 1 currently supports JPG for secondary outputs")
        return normalized


class ModelsConfig(StrictModel):
    hermes: str = "deepseek/deepseek-v4.1-flash-1017"
    visual_decisions: str = "typesafe/jev-1.14"
    escalation: str = "google/gemini-3-flash-preview"


class CloudProcessingConfig(StrictModel):
    enabled: bool = False


class AppConfig(StrictModel):
    paths: PathsConfig
    collection: str = "wedding"
    photo: PhotoConfig = Field(default_factory=PhotoConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    cloud_processing: CloudProcessingConfig = Field(default_factory=CloudProcessingConfig)


def load_config(config_path: Path | str | None = None) -> AppConfig:
    """Load YAML config, allowing VICTORIYA_ROOT to override its root path.

    API keys are intentionally not read from YAML. They are supplied through
    environment variables or a local secret manager by the later API adapters.
    """
    if config_path is None:
        config_path = os.environ.get("VICTORIYA_CONFIG", "config/config.yaml")

    path = Path(config_path).expanduser()
    if not path.is_file():
        raise ConfigurationError(
            f"Configuration file not found: {path}. "
            "Copy config/config.example.yaml to config/config.yaml first."
        )

    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Cannot read configuration file {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration must be a YAML object at the top level")

    root_override = os.environ.get("VICTORIYA_ROOT")
    if root_override:
        paths = raw.setdefault("paths", {})
        if not isinstance(paths, dict):
            raise ConfigurationError("'paths' must be a YAML object")
        paths["victoriya_root"] = root_override

    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise ConfigurationError(f"Invalid configuration: {details}") from exc
