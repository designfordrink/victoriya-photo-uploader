from __future__ import annotations

from pathlib import Path

import pytest

from victoriya_photo.storage import PathManager, UnsafePathError


def test_root_is_created_and_writable(tmp_path: Path) -> None:
    root = tmp_path / "Victoriya"
    manager = PathManager(root)

    actual_root = manager.ensure_writable_root()

    assert actual_root.is_dir()
    assert list(root.iterdir()) == []


@pytest.mark.parametrize(
    "parts",
    [
        ("..", "outside"),
        ("Collections", "..", "outside"),
        ("C:\\outside",),
        ("folder/name",),
        ("folder\\name",),
        ("CON",),
        ("trailing.",),
        ("trailing ",),
    ],
)
def test_rejects_unsafe_path_components(tmp_path: Path, parts: tuple[str, ...]) -> None:
    manager = PathManager(tmp_path / "Victoriya")

    with pytest.raises(UnsafePathError):
        manager.safe_path(*parts)


def test_builds_product_directories_inside_root(tmp_path: Path) -> None:
    root = tmp_path / "Victoriya"
    manager = PathManager(root)
    manager.ensure_writable_root()

    directories = manager.product_directories(
        collection="wedding",
        brand="Pronovias",
        model="SUFI",
        job_id="job-001",
    )

    assert directories.product_root == root / "Collections" / "wedding" / "Pronovias" / "SUFI"
    assert directories.source_dir.is_dir()
    assert directories.work_dir.is_dir()
    assert directories.output_dir.is_dir()
    assert directories.reports_dir.is_dir()


def test_rejects_symlink_escape_when_supported(tmp_path: Path) -> None:
    root = tmp_path / "Victoriya"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "escape"

    try:
        link.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("Symlink creation is not available in this environment")

    manager = PathManager(root)
    with pytest.raises(UnsafePathError):
        manager.safe_path("escape", "secret.txt")
