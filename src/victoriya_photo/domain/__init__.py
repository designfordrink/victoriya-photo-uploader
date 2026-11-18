"""Typed domain models and workflow rules for photo preparation jobs."""

from victoriya_photo.domain.models import (
    Asset,
    AssetOutput,
    AssetSelection,
    AssetSource,
    JobError,
    JobPaths,
    JobStatus,
    PhotoJob,
    ProcessingResult,
    ProductIdentity,
    StateTransition,
    Usage,
    WatermarkBox,
    WatermarkResult,
    WatermarkStatus,
)
from victoriya_photo.domain.state_machine import (
    InvalidStateTransition,
    JobStateMachine,
)

__all__ = [
    "Asset",
    "AssetOutput",
    "AssetSelection",
    "AssetSource",
    "InvalidStateTransition",
    "JobError",
    "JobPaths",
    "JobStateMachine",
    "JobStatus",
    "PhotoJob",
    "ProcessingResult",
    "ProductIdentity",
    "StateTransition",
    "Usage",
    "WatermarkBox",
    "WatermarkResult",
    "WatermarkStatus",
]
