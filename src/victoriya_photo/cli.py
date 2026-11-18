"""Small bootstrap CLI for local setup diagnostics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from victoriya_photo.config import ConfigurationError, load_config
from victoriya_photo.storage import PathManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="victoriya-photo",
        description="Local setup checks for Victoriya Photo Assistant.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser(
        "doctor",
        help="Validate the local config and check the Victoriya folder.",
    )
    doctor.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config YAML (default: VICTORIYA_CONFIG or config/config.yaml).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "doctor":
        try:
            config = load_config(args.config)
            root = PathManager(config.paths.victoriya_root).ensure_writable_root()
        except (ConfigurationError, OSError, ValueError) as exc:
            print(f"Проверка не пройдена: {exc}", file=sys.stderr)
            return 1

        print("Конфигурация корректна.")
        print(f"Папка данных доступна для записи: {root}")
        print(f"Коллекция по умолчанию: {config.collection}")
        print(f"Размер главного фото: {config.photo.main_width} × {config.photo.main_height} px")
        print(
            "Обработка через облачные сервисы: "
            f"{'включена' if config.cloud_processing.enabled else 'выключена'}"
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
