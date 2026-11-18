"""Guarded lifecycle transitions for a PhotoJob."""

from __future__ import annotations

from datetime import datetime
from typing import Final

from victoriya_photo.domain.models import JobStatus, PhotoJob, StateTransition, utc_now


class InvalidStateTransition(ValueError):
    """Raised when a job is moved through a forbidden state transition."""


_ALLOWED_TRANSITIONS: Final[dict[JobStatus, frozenset[JobStatus]]] = {
    JobStatus.CREATED: frozenset({JobStatus.VALIDATING_URL}),
    JobStatus.VALIDATING_URL: frozenset({JobStatus.PAGE_OPENED}),
    JobStatus.PAGE_OPENED: frozenset({JobStatus.GALLERY_DISCOVERED}),
    JobStatus.GALLERY_DISCOVERED: frozenset({JobStatus.SOURCES_DOWNLOADED}),
    JobStatus.SOURCES_DOWNLOADED: frozenset({JobStatus.ANALYZING_ASSETS}),
    JobStatus.ANALYZING_ASSETS: frozenset({JobStatus.LEAD_SELECTED, JobStatus.NEEDS_REVIEW}),
    JobStatus.LEAD_SELECTED: frozenset({JobStatus.PROCESSING, JobStatus.NEEDS_REVIEW}),
    JobStatus.PROCESSING: frozenset({JobStatus.VALIDATING_OUTPUT, JobStatus.NEEDS_REVIEW}),
    JobStatus.VALIDATING_OUTPUT: frozenset(
        {JobStatus.COMPLETED, JobStatus.PARTIAL, JobStatus.NEEDS_REVIEW}
    ),
    JobStatus.COMPLETED: frozenset(),
    JobStatus.PARTIAL: frozenset(),
    JobStatus.NEEDS_REVIEW: frozenset(),
    JobStatus.FAILED: frozenset(),
}


class JobStateMachine:
    """Apply only transitions allowed by the accepted job lifecycle."""

    def transition(
        self,
        job: PhotoJob,
        target: JobStatus,
        occurred_at: datetime | None = None,
    ) -> PhotoJob:
        current = job.status
        allowed = set(_ALLOWED_TRANSITIONS[current])
        if target == JobStatus.FAILED and current not in {
            JobStatus.COMPLETED, JobStatus.PARTIAL, JobStatus.NEEDS_REVIEW, JobStatus.FAILED,
        }:
            allowed.add(JobStatus.FAILED)

        if target not in allowed:
            raise InvalidStateTransition(
                f"Cannot move job from {current.value} to {target.value}"
            )

        timestamp = occurred_at or utc_now()
        job.status = target
        job.updated_at = timestamp
        job.status_history.append(
            StateTransition(from_status=current, to_status=target, occurred_at=timestamp)
        )
        return job
