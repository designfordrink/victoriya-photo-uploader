from victoriya_photo.domain.models import PhotoJob, ProductIdentity
from victoriya_photo.storage.manager import StorageManager
from victoriya_photo.storage.paths import PathManager


def test_storage_manager_creates_product_layout_and_relative_paths(tmp_path) -> None:
    root = tmp_path / "Victoriya"
    manager = StorageManager(PathManager(root))
    job = PhotoJob(
        source_url="https://manufacturer.example/dress",
        product=ProductIdentity(brand="Pronovias", model="SUFI"),
    )
    prepared = manager.prepare_job(job)
    directories = prepared.directories

    assert directories.source_dir.is_dir()
    assert directories.work_dir.is_dir()
    assert directories.output_dir.is_dir()
    assert directories.reports_dir.is_dir()
    assert job.paths is not None
    assert job.paths.product_root == "Collections/wedding/Pronovias/SUFI"
    assert job.paths.report_json == f"reports/{job.job_id}.json"
    assert directories.product_root.is_relative_to(root)
