from __future__ import annotations

from pathlib import Path

import pytest

from victoriya_photo.config import ConfigurationError, load_config


def test_loads_valid_config(tmp_path: Path) -> None:
    root = tmp_path / "Victoriya"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
paths:
  victoriya_root: "{root.as_posix()}"
collection: wedding
photo:
  main_width: 600
  main_height: 800
  secondary_max_bytes: 2500000
  secondary_format: jpg
cloud_processing:
  enabled: false
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.paths.victoriya_root == root
    assert config.collection == "wedding"
    assert config.photo.main_width == 600
    assert config.photo.main_height == 800
    assert config.photo.secondary_max_bytes == 2_500_000
    assert config.cloud_processing.enabled is False


def test_environment_root_overrides_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_file = tmp_path / "config.yaml"
    old_root = (tmp_path / "old").as_posix()
    config_file.write_text(
        f'paths:\n  victoriya_root: "{old_root}"\n',
        encoding="utf-8",
    )
    override = tmp_path / "override"
    monkeypatch.setenv("VICTORIYA_ROOT", str(override))

    config = load_config(config_file)

    assert config.paths.victoriya_root == override


def test_missing_config_has_actionable_message(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="Copy config/config.example.yaml"):
        load_config(tmp_path / "missing.yaml")


def test_relative_root_is_rejected(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("paths:\n  victoriya_root: relative/path\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="absolute path"):
        load_config(config_file)


def test_unknown_config_keys_are_rejected(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f'paths:\n  victoriya_root: "{tmp_path.as_posix()}"\n'
        "unexpected: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="Extra inputs are not permitted"):
        load_config(config_file)
