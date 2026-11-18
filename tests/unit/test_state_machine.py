import pytest

from victoriya_photo.domain.models import JobStatus, PhotoJob, ProductIdentity
from victoriya_photo.domain.state_machine import InvalidStateTransition, JobStateMachine


def make_job() -> PhotoJob:
    return PhotoJob(
        source_url="https://manufacturer.example/dress",
        product=ProductIdentity(brand="Pronovias", model="SUFI"),
    )


def test_happy_path_transitions_to_completed() -> None:
    job = make_job()
    machine = JobStateMachine()
    statuses = [
        JobStatus.VALIDATING_URL, JobStatus.PAGE_OPENED,
        JobStatus.GALLERY_DISCOVERED, JobStatus.SOURCES_DOWNLOADED,
        JobStatus.ANALYZING_ASSETS, JobStatus.LEAD_SELECTED,
        JobStatus.PROCESSING, JobStatus.VALIDATING_OUTPUT, JobStatus.COMPLETED,
    ]
    for status in statuses:
        machine.transition(job, status)
    assert job.status is JobStatus.COMPLETED
    assert len(job.status_history) == len(statuses)


def test_failed_is_allowed_from_nonterminal_state() -> None:
    job = make_job()
    JobStateMachine().transition(job, JobStatus.FAILED)
    assert job.status is JobStatus.FAILED


@pytest.mark.parametrize(
    ("initial", "target"),
    [
        (JobStatus.CREATED, JobStatus.PROCESSING),
        (JobStatus.SOURCES_DOWNLOADED, JobStatus.COMPLETED),
        (JobStatus.COMPLETED, JobStatus.FAILED),
        (JobStatus.NEEDS_REVIEW, JobStatus.PROCESSING),
    ],
)
def test_forbidden_transitions_are_rejected(initial: JobStatus, target: JobStatus) -> None:
    job = make_job()
    job.status = initial
    with pytest.raises(InvalidStateTransition):
        JobStateMachine().transition(job, target)
    assert job.status is initial


def test_needs_review_is_reachable_from_analysis() -> None:
    job = make_job()
    job.status = JobStatus.ANALYZING_ASSETS
    JobStateMachine().transition(job, JobStatus.NEEDS_REVIEW)
    assert job.status is JobStatus.NEEDS_REVIEW
