"""Pydantic schemas for jobs, assets, analysis, and processing results."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)


class StrictModel(BaseModel):
    """Base model that rejects unknown data and validates assignments."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)


class JobStatus(StrEnum):
    CREATED = "CREATED"
    VALIDATING_URL = "VALIDATING_URL"
    PAGE_OPENED = "PAGE_OPENED"
    GALLERY_DISCOVERED = "GALLERY_DISCOVERED"
    SOURCES_DOWNLOADED = "SOURCES_DOWNLOADED"
    ANALYZING_ASSETS = "ANALYZING_ASSETS"
    LEAD_SELECTED = "LEAD_SELECTED"
    PROCESSING = "PROCESSING"
    VALIDATING_OUTPUT = "VALIDATING_OUTPUT"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class WatermarkStatus(StrEnum):
    ABSENT = "absent"
    PRESENT = "present"
    UNCERTAIN = "uncertain"
    REMOVED = "removed"
    NEEDS_REVIEW = "needs_review"


class ProductIdentity(StrictModel):
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=120)
    collection: str = Field(default="wedding", min_length=1, max_length=80)
    identity_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class JobPaths(StrictModel):
    """Paths stored in a manifest are relative to their documented root."""
    product_root: str
    source_dir: str
    work_dir: str
    output_dir: str
    report_json: str

    @field_validator("product_root", "source_dir", "work_dir", "output_dir", "report_json")
    @classmethod
    def relative_path_only(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        posix = PurePosixPath(normalized)
        windows = PureWindowsPath(normalized)
        if not normalized or posix.is_absolute() or windows.is_absolute() or windows.drive:
            raise ValueError("Manifest paths must be non-empty relative paths")
        if any(part in {"", ".", ".."} for part in posix.parts):
            raise ValueError("Manifest paths cannot contain traversal components")
        return normalized


class WatermarkBox(StrictModel):
    left: float = Field(ge=0.0, le=1.0)
    top: float = Field(ge=0.0, le=1.0)
    right: float = Field(gt=0.0, le=1.0)
    bottom: float = Field(gt=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_box_geometry(self) -> WatermarkBox:
        if self.left >= self.right or self.top >= self.bottom:
            raise ValueError("Watermark box must have positive width and height")
        return self


class WatermarkResult(StrictModel):
    status: WatermarkStatus = WatermarkStatus.UNCERTAIN
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    checked_model: str | None = None
    checked_at: datetime | None = None
    box: WatermarkBox | None = None
    mask_path: str | None = None
    backend: str | None = None
    removal_status: str | None = None


class AssetSource(StrictModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    format: str = Field(min_length=1, max_length=16)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    bytes: int = Field(gt=0)


class AssetSelection(StrictModel):
    is_lead_candidate: bool = False
    front_facing: float | None = Field(default=None, ge=0.0, le=1.0)
    full_length: float | None = Field(default=None, ge=0.0, le=1.0)
    dress_visible: float | None = Field(default=None, ge=0.0, le=1.0)
    image_quality: float | None = Field(default=None, ge=0.0, le=1.0)
    lead_score: float | None = Field(default=None, ge=0.0, le=1.0)
    selected_as_lead: bool = False
    fallback: bool = False


class ProcessingResult(StrictModel):
    """Processing decisions and providers used for one asset."""
    method: str | None = None
    outpaint_provider: str | None = None
    erase_provider: str | None = None
    seed: int | None = None


class AssetOutput(StrictModel):
    relative_path: str = Field(min_length=1)
    format: str = Field(min_length=1, max_length=16)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    validated: bool = False


class Asset(StrictModel):
    asset_id: str = Field(min_length=1, max_length=100)
    gallery_order: int = Field(ge=1)
    source: AssetSource
    watermark: WatermarkResult = Field(default_factory=WatermarkResult)
    selection: AssetSelection = Field(default_factory=AssetSelection)
    processing: ProcessingResult | None = None
    output: AssetOutput | None = None
    warnings: list[str] = Field(default_factory=list)


class JobError(StrictModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=utc_now)


class Usage(StrictModel):
    openrouter_cost_usd: float = Field(default=0.0, ge=0.0)
    stability_credits: int = Field(default=0, ge=0)


class StateTransition(StrictModel):
    from_status: JobStatus
    to_status: JobStatus
    occurred_at: datetime = Field(default_factory=utc_now)


class PhotoJob(StrictModel):
    job_id: UUID = Field(default_factory=uuid4)
    schema_version: str = "1.0"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    status: JobStatus = JobStatus.CREATED
    source_url: str = Field(min_length=1, max_length=2048)
    product: ProductIdentity
    paths: JobPaths | None = None
    assets: list[Asset] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[JobError] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    status_history: list[StateTransition] = Field(default_factory=list)

    @field_validator("created_at", "updated_at")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Job timestamps must include a timezone")
        return value

    @field_validator("source_url")
    @classmethod
    def trim_source_url(cls, value: str) -> str:
        return value.strip()

    def model_json_dict(self) -> dict[str, Any]:
        """Return a JSON-ready manifest dictionary."""
        return self.model_dump(mode="json")
