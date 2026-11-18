"""Resolve all photo-job paths safely inside the configured root."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Final
import re


class UnsafePathError(ValueError):
    """Raised when a requested path would escape the configured data root."""


_WINDOWS_RESERVED_NAMES: Final[set[str]] = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
_INVALID_WINDOWS_CHARS: Final[re.Pattern[str]] = re.compile(r'[<>:"|?*]')


@dataclass(frozen=True)
class ProductDirectories:
    """Directories belonging to one product and processing job."""

    product_root: Path
    source_dir: Path
    work_dir: Path
    output_dir: Path
    reports_dir: Path


class PathManager:
    """Build paths and prevent path traversal or symlink escapes.

    The configured root is trusted because the user selected it explicitly.
    Every child path is resolved and checked against that root before use.
    """

    def __init__(self, root: Path | str) -> None:
        candidate = Path(root).expanduser()
        if not candidate.is_absolute():
            raise UnsafePathError("Victoriya root must be an absolute path")
        self._root = candidate.resolve(strict=False)

    @property
    def root(self) -> Path:
        """Return the normalized absolute data root."""
        return self._root

    def safe_path(self, *parts: str) -> Path:
        """Resolve safe relative path parts under the configured root."""
        candidate = self._root

        for part in parts:
            self._validate_segment(part)
            candidate = candidate / part

        resolved = candidate.resolve(strict=False)
        if not self._is_inside_root(resolved):
            raise UnsafePathError("Requested path resolves outside the Victoriya root")
        return resolved

    def ensure_writable_root(self) -> Path:
        """Create the root if needed and verify that it is writable."""
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            resolved_root = self._root.resolve(strict=True)
            if not resolved_root.is_dir():
                raise UnsafePathError("Victoriya root exists but is not a directory")
            self._root = resolved_root

            probe_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    prefix=".victoriya-write-test-",
                    dir=self._root,
                    delete=False,
                ) as probe:
                    probe.write(b"victoriya-write-check")
                    probe_path = Path(probe.name)
            finally:
                if probe_path is not None:
                    probe_path.unlink(missing_ok=True)
        except UnsafePathError:
            raise
        except OSError as exc:
            raise OSError(f"Victoriya root is not writable: {self._root}: {exc}") from exc

        return self._root

    def product_directories(
        self,
        collection: str,
        brand: str,
        model: str,
        job_id: str,
    ) -> ProductDirectories:
        """Create and return the source/work/output/report directories."""
        product_root = self.safe_path("Collections", collection, brand, model)
        source_dir = self.safe_path(
            "Collections", collection, brand, model, "source", job_id
        )
        work_dir = self.safe_path(
            "Collections", collection, brand, model, "source", job_id, "work"
        )
        output_dir = self.safe_path("Collections", collection, brand, model, "output")
        reports_dir = self.safe_path("Collections", collection, brand, model, "reports")

        for directory in (source_dir, work_dir, output_dir, reports_dir):
            directory.mkdir(parents=True, exist_ok=True)
            resolved = directory.resolve(strict=True)
            if not self._is_inside_root(resolved):
                raise UnsafePathError("A directory resolves outside the Victoriya root")

        return ProductDirectories(
            product_root=product_root,
            source_dir=source_dir,
            work_dir=work_dir,
            output_dir=output_dir,
            reports_dir=reports_dir,
        )

    def _validate_segment(self, segment: str) -> None:
        if not isinstance(segment, str) or not segment:
            raise UnsafePathError("Path components must be non-empty strings")
        if segment in {".", ".."}:
            raise UnsafePathError("Relative traversal components are not allowed")
        if "/" in segment or "\\" in segment:
            raise UnsafePathError("Path components cannot contain path separators")
        if Path(segment).is_absolute() or PureWindowsPath(segment).drive:
            raise UnsafePathError("Absolute paths and drive prefixes are not allowed")
        if _INVALID_WINDOWS_CHARS.search(segment):
            raise UnsafePathError("Path component contains characters not allowed on Windows")
        if any(ord(character) < 32 for character in segment):
            raise UnsafePathError("Path components cannot contain control characters")
        if segment.endswith((" ", ".")):
            raise UnsafePathError("Path components cannot end with a space or period")
        device_name = segment.split(".", maxsplit=1)[0].upper()
        if device_name in _WINDOWS_RESERVED_NAMES:
            raise UnsafePathError("Path component is a reserved Windows device name")

    def _is_inside_root(self, candidate: Path) -> bool:
        try:
            candidate.relative_to(self._root)
        except ValueError:
            return False
        return True
