import pytest

from victoriya_photo.domain.models import PhotoJob, ProductIdentity
from victoriya_photo.jobs.repository import (
    JobAlreadyExistsError, JobNotFoundError, JobRepository,
)
from victoriya_photo.storage.paths import PathManager


def make_job() -> PhotoJob:
    return PhotoJob(
        source_url="https://manufacturer.example/dress",
        product=ProductIdentity(brand="Pronovias", model="SUFI"),
    )


def test_repository_create_get_and_save(tmp_path) -> None:
    repository = JobRepository(PathManager(tmp_path / "Victoriya"))
    job = make_job()
    repository.create(job)
    loaded = repository.get(job.job_id)
    assert loaded.job_id == job.job_id
    assert loaded.product.model == "SUFI"
    loaded.warnings.append("Test warning")
    repository.save(loaded)
    assert repository.get(job.job_id).warnings == ["Test warning"]


def test_repository_never_replaces_a_created_job(tmp_path) -> None:
    repository = JobRepository(PathManager(tmp_path / "Victoriya"))
    job = make_job()
    repository.create(job)
    with pytest.raises(JobAlreadyExistsError):
        repository.create(job)


def test_repository_unknown_job_raises_clear_error(tmp_path) -> None:
    repository = JobRepository(PathManager(tmp_path / "Victoriya"))
    with pytest.raises(JobNotFoundError):
        repository.get("00000000-0000-0000-0000-000000000001")


def test_repository_rejects_non_uuid_ids(tmp_path) -> None:
    repository = JobRepository(PathManager(tmp_path / "Victoriya"))
    with pytest.raises(ValueError, match="UUID"):
        repository.get("../../outside")
