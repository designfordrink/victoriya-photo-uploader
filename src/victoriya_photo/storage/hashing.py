"""Content hashing, exact deduplication, and no-overwrite file operations."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Protocol


class HasSha256(Protocol):
    sha256: str


class FileCollisionError(FileExistsError):
    """Raised when a target exists with different content."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calculate a file's SHA-256 without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def unique_by_sha256[T: HasSha256](items: list[T]) -> list[T]:
    """Keep the first item for each exact SHA-256; similar images remain distinct."""
    seen: set[str] = set()
    unique: list[T] = []
    for item in items:
        key = item.sha256.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def copy_file_no_overwrite(source: Path, destination: Path) -> bool:
    """Copy a file once; return False for identical existing content.

    A different existing file is never replaced. The source is read-only.
    """
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different files")

    source_hash = sha256_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as input_file, destination.open("xb") as output_file:
            shutil.copyfileobj(input_file, output_file)
            output_file.flush()
    except FileExistsError as exc:
        if sha256_file(destination) == source_hash:
            return False
        raise FileCollisionError(
            f"Refusing to overwrite a different file: {destination}"
        ) from exc
    except OSError:
        destination.unlink(missing_ok=True)
        raise

    if sha256_file(destination) != source_hash:
        destination.unlink(missing_ok=True)
        raise OSError(f"Copied file failed SHA-256 verification: {destination}")
    return True
