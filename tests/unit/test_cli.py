from __future__ import annotations

from pathlib import Path

import pytest

from victoriya_photo.cli import main


def test_doctor_command_succeeds(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "Victoriya"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f'paths:\n  victoriya_root: "{root.as_posix()}"\n',
        encoding="utf-8",
    )

    exit_code = main(["doctor", "--config", str(config_file)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Конфигурация корректна." in captured.out
    assert root.is_dir()


def test_doctor_command_returns_error_for_missing_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["doctor", "--config", str(tmp_path / "missing.yaml")])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Проверка не пройдена" in captured.err
