"""Write a durable JSON manifest to the product's reports directory."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from victoriya_photo.domain.models import PhotoJob
from victoriya_photo.storage.manager import StorageManager


class ManifestWriter:
    def __init__(self, storage: StorageManager) -> None:
        self._storage = storage

    def write(self, job: PhotoJob) -> Path:
        """Atomically write the current job manifest and return its path."""
        storage = self._storage.prepare_job(job)
        destination = storage.source_manifest_path
        payload = json.dumps(job.model_json_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=destination.parent,
                prefix=f".{job.job_id}.", suffix=".tmp", delete=False,
            ) as temporary:
                temporary.write(payload + "\n")
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, destination)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        return destination

    def read(self, path: Path) -> PhotoJob:
        """Read a manifest through the typed PhotoJob schema."""
        return PhotoJob.model_validate_json(path.read_text(encoding="utf-8"))
