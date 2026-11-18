"""Render a concise Markdown report for a completed or in-progress job."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from victoriya_photo.domain.models import PhotoJob
from victoriya_photo.storage.manager import StorageManager


class MarkdownReportWriter:
    def __init__(self, storage: StorageManager) -> None:
        self._storage = storage

    def render(self, job: PhotoJob) -> str:
        lines = [
            f"# Photo preparation — {job.product.brand} / {job.product.model}",
            "",
            f"- **Job ID:** `{job.job_id}`",
            f"- **Status:** `{job.status.value}`",
            f"- **Source URL:** {job.source_url}",
            f"- **Created:** {job.created_at.isoformat()}",
            f"- **Updated:** {job.updated_at.isoformat()}",
            "",
            "## Assets",
            "",
        ]
        if not job.assets:
            lines.append("No assets recorded yet.")
        else:
            lines.extend(
                [
                    "| Asset | Source | Watermark | Output | Warnings |",
                    "|---|---|---|---|---|",
                ]
            )
            for asset in job.assets:
                output = asset.output.relative_path if asset.output else "—"
                warning_text = "; ".join(asset.warnings).replace("|", "\\|") or "—"
                source_path = asset.source.relative_path.replace("|", "\\|")
                lines.append(
                    f"| {asset.asset_id} | {source_path} | "
                    f"{asset.watermark.status.value} | {output} | {warning_text} |"
                )
        if job.warnings:
            lines.extend(["", "## Warnings", ""])
            lines.extend(f"- {warning}" for warning in job.warnings)
        if job.errors:
            lines.extend(["", "## Errors", ""])
            lines.extend(f"- **{error.code}:** {error.message}" for error in job.errors)
        lines.extend(["", "## Usage", ""])
        lines.append(f"- OpenRouter cost: ${job.usage.openrouter_cost_usd:.4f}")
        lines.append(f"- Stability credits: {job.usage.stability_credits}")
        lines.append("")
        return "\n".join(lines)

    def write(self, job: PhotoJob) -> Path:
        """Atomically refresh the Markdown report; original photos are unaffected."""
        storage = self._storage.prepare_job(job)
        destination = storage.markdown_report_path
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=destination.parent,
                prefix=f".{job.job_id}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(self.render(job))
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, destination)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        return destination
