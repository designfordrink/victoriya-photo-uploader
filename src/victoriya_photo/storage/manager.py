"""Product-scoped storage orchestration built on the safe PathManager."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from victoriya_photo.domain.models import PhotoJob
from victoriya_photo.storage.hashing import copy_file_no_overwrite
from victoriya_photo.storage.paths import PathManager, ProductDirectories


@dataclass(frozen=True)
class PreparedJobStorage:
    directories: ProductDirectories
    source_manifest_path: Path
    markdown_report_path: Path


class StorageManager:
    """Create and resolve source/work/output/report folders for a product job."""

    def __init__(self, path_manager: PathManager) -> None:
        self.path_manager = path_manager

    def prepare_job(self, job: PhotoJob) -> PreparedJobStorage:
        """Create the approved folder layout and persist relative paths in the job."""
        directories = self.path_manager.product_directories(
            collection=job.product.collection,
            brand=job.product.brand,
            model=job.product.model,
            job_id=str(job.job_id),
        )
        root = self.path_manager.root
        job.paths = {
            "product_root": directories.product_root.relative_to(root).as_posix(),
            "source_dir": directories.source_dir.relative_to(directories.product_root).as_posix(),
            "work_dir": directories.work_dir.relative_to(directories.product_root).as_posix(),
            "output_dir": directories.output_dir.relative_to(directories.product_root).as_posix(),
            "report_json": f"reports/{job.job_id}.json",
        }
        return PreparedJobStorage(
            directories=directories,
            source_manifest_path=directories.reports_dir / f"{job.job_id}.json",
            markdown_report_path=directories.reports_dir / f"{job.job_id}.md",
        )

    def save_original(self, source: Path, destination: Path) -> bool:
        """Copy an original into storage without ever replacing existing content."""
        safe_destination = destination.resolve(strict=False)
        if not safe_destination.is_relative_to(self.path_manager.root):
            raise ValueError("Original destination must stay inside the Victoriya root")
        return copy_file_no_overwrite(source, safe_destination)

    def safe_path(self, *parts: str) -> Path:
        """Expose the configured root's safe path resolver to storage clients."""
        return self.path_manager.safe_path(*parts)
