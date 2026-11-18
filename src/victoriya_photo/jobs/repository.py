"""JSON-backed repository for PhotoJob records."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from victoriya_photo.domain.models import PhotoJob
from victoriya_photo.storage.paths import PathManager


class JobRepositoryError(RuntimeError):
    """Base repository error."""


class JobAlreadyExistsError(JobRepositoryError):
    """Raised when create is called for an existing job ID."""


class JobNotFoundError(JobRepositoryError):
    """Raised when a requested job does not exist."""


class JobRepository:
    """Persist current job state in a local JSON file under the configured root."""

    def __init__(self, path_manager: PathManager) -> None:
        self._paths = path_manager
        self._jobs_dir = self._paths.safe_path("jobs")
        self._jobs_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, job_id: UUID | str) -> Path:
        try:
            normalized_id = UUID(str(job_id))
        except ValueError as exc:
            raise ValueError("job_id must be a UUID") from exc
        return self._paths.safe_path("jobs", f"{normalized_id}.json")

    def create(self, job: PhotoJob) -> PhotoJob:
        """Create a new job record. Existing records are never replaced."""
        path = self._path_for(job.job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._serialize(job)
        try:
            with path.open("x", encoding="utf-8", newline="\n") as target:
                target.write(payload)
                target.flush()
                os.fsync(target.fileno())
        except FileExistsError as exc:
            raise JobAlreadyExistsError(f"Job already exists: {job.job_id}") from exc
        return job

    def get(self, job_id: UUID | str) -> PhotoJob:
        """Read and validate a stored job."""
        path = self._path_for(job_id)
        if not path.is_file():
            raise JobNotFoundError(f"Job not found: {job_id}")
        try:
            return PhotoJob.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValidationError) as exc:
            raise JobRepositoryError(f"Cannot read job {job_id}: {exc}") from exc

    def save(self, job: PhotoJob) -> PhotoJob:
        """Atomically replace an existing job record after a state update."""
        path = self._path_for(job.job_id)
        if not path.is_file():
            raise JobNotFoundError(f"Job not found: {job.job_id}")
        payload = self._serialize(job)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=path.parent,
                prefix=f".{job.job_id}.", suffix=".tmp", delete=False,
            ) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise JobRepositoryError(f"Cannot save job {job.job_id}: {exc}") from exc
        return job

    def _serialize(self, job: PhotoJob) -> str:
        data = job.model_json_dict()
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
