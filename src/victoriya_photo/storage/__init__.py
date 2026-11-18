"""Safe local storage helpers."""

from victoriya_photo.storage.hashing import (
    FileCollisionError,
    copy_file_no_overwrite,
    sha256_file,
    unique_by_sha256,
)
from victoriya_photo.storage.manager import PreparedJobStorage, StorageManager
from victoriya_photo.storage.paths import PathManager, ProductDirectories, UnsafePathError

__all__ = [
    "FileCollisionError",
    "PathManager",
    "PreparedJobStorage",
    "ProductDirectories",
    "StorageManager",
    "UnsafePathError",
    "copy_file_no_overwrite",
    "sha256_file",
    "unique_by_sha256",
]
