import json

from victoriya_photo.domain.models import PhotoJob, ProductIdentity
from victoriya_photo.reporting import ManifestWriter, MarkdownReportWriter
from victoriya_photo.storage.manager import StorageManager
from victoriya_photo.storage.paths import PathManager


def make_job() -> PhotoJob:
    return PhotoJob(
        source_url="https://manufacturer.example/dress",
        product=ProductIdentity(brand="Pronovias", model="SUFI"),
        warnings=["Visual review recommended"],
    )


def test_manifest_is_written_and_can_be_read_back(tmp_path) -> None:
    storage = StorageManager(PathManager(tmp_path / "Victoriya"))
    writer = ManifestWriter(storage)
    job = make_job()
    path = writer.write(job)
    payload = json.loads(path.read_text(encoding="utf-8"))
    restored = writer.read(path)

    assert payload["job_id"] == str(job.job_id)
    assert restored.job_id == job.job_id
    assert restored.warnings == ["Visual review recommended"]


def test_markdown_report_contains_job_and_warnings(tmp_path) -> None:
    storage = StorageManager(PathManager(tmp_path / "Victoriya"))
    writer = MarkdownReportWriter(storage)
    job = make_job()
    path = writer.write(job)
    content = path.read_text(encoding="utf-8")

    assert "Pronovias / SUFI" in content
    assert str(job.job_id) in content
    assert "Visual review recommended" in content
