"""Deterministic semantic validation beyond the draft JSON Schema."""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Mapping
from uuid import UUID


class ValidationError(ValueError):
    """A stable, human-readable SAP boundary validation error."""


def require_fields(value: Mapping[str, Any], fields: tuple[str, ...], context: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ValidationError(f"{context}: missing required fields {missing}")


def validate_uuid(value: str, field: str) -> None:
    try:
        UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"{field}: invalid UUID") from exc


def validate_datetime(value: str, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"{field}: invalid RFC 3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{field}: timezone is required")


def validate_clock(value: Mapping[str, Any]) -> None:
    require_fields(value, ("clock_id", "sync_source", "uncertainty_ms"), "clock")
    if not value["clock_id"]:
        raise ValidationError("clock.clock_id: empty")
    if value["sync_source"] not in {
        "none",
        "system",
        "ntp",
        "ptp",
        "shared_audio",
        "measured_offset",
        "simulation",
    }:
        raise ValidationError("clock.sync_source: unsupported")
    if not isinstance(value["uncertainty_ms"], (int, float)) or value["uncertainty_ms"] < 0:
        raise ValidationError("clock.uncertainty_ms: must be non-negative")


def validate_pose(value: Mapping[str, Any]) -> None:
    require_fields(
        value,
        ("frame_id", "position_m", "orientation", "status", "confidence"),
        "pose",
    )
    if not value["frame_id"]:
        raise ValidationError("pose.frame_id: empty")
    position = value["position_m"]
    require_fields(position, ("x", "y", "z"), "pose.position_m")
    quaternion = value["orientation"]
    require_fields(quaternion, ("x", "y", "z", "w"), "pose.orientation")
    norm = math.sqrt(sum(float(quaternion[key]) ** 2 for key in ("x", "y", "z", "w")))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ValidationError("pose.orientation: quaternion must be normalized")
    confidence = value["confidence"]
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValidationError("pose.confidence: must be in [0, 1]")
    covariance = value.get("covariance_6x6")
    if covariance is not None and len(covariance) != 36:
        raise ValidationError("pose.covariance_6x6: must contain 36 values")
