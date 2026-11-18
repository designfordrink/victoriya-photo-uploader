from datetime import datetime

import pytest
from pydantic import ValidationError

from victoriya_photo.domain.models import (
    Asset,
    AssetSource,
    JobStatus,
    PhotoJob,
    ProductIdentity,
    WatermarkBox,
    WatermarkStatus,
)


def make_job() -> PhotoJob:
    return PhotoJob(
        source_url="https://manufacturer.example/dress",
        product=ProductIdentity(brand="Pronovias", model="SUFI"),
    )


def test_job_defaults_and_json_round_trip() -> None:
    job = make_job()
    restored = PhotoJob.model_validate_json(job.model_dump_json())
    assert restored.job_id == job.job_id
    assert restored.status is JobStatus.CREATED
    assert restored.product.collection == "wedding"
    assert restored.created_at.tzinfo is not None


def test_asset_source_requires_valid_hash_and_dimensions() -> None:
    source = AssetSource(
        relative_path="source/original.webp",
        sha256="a" * 64,
        format="WEBP",
        width=1800,
        height=2400,
        bytes=12345,
    )
    assert source.width == 1800
    with pytest.raises(ValidationError):
        AssetSource(
            relative_path="source/original.webp",
            sha256="not-a-hash",
            format="WEBP",
            width=0,
            height=2400,
            bytes=12345,
        )


def test_watermark_box_rejects_invalid_geometry() -> None:
    with pytest.raises(ValidationError):
        WatermarkBox(left=0.8, top=0.1, right=0.2, bottom=0.9, confidence=0.9)


def test_watermark_uncertain_is_safe_default() -> None:
    asset = Asset(
        asset_id="asset-001",
        gallery_order=1,
        source=AssetSource(
            relative_path="source/a.jpg",
            sha256="b" * 64,
            format="JPEG",
            width=600,
            height=800,
            bytes=1000,
        ),
    )
    assert asset.watermark.status is WatermarkStatus.UNCERTAIN
    assert asset.watermark.checked_at is None


def test_job_rejects_naive_timestamps() -> None:
    with pytest.raises(ValidationError):
        PhotoJob(
            source_url="https://manufacturer.example/dress",
            product=ProductIdentity(brand="Brand", model="Model"),
            created_at=datetime(2026, 11, 18),
        )
