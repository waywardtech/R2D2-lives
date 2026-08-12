"""Content-addressed capability evidence recording and replay."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def build_hil_failure_evidence(
    *,
    error_type: str,
    owner_state: str,
    driver_connected: bool,
    driver_stopped: bool,
    error_stage: str | None = None,
) -> dict[str, object]:
    """Build sanitized terminal evidence without exception text or device identity."""

    evidence: dict[str, object] = {
        "schema_version": "1.0",
        "evidence_category": "HIL-stationary-failure",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "terminal": "failed",
        "error_type": error_type,
        "owner_state": owner_state,
        "driver_connected": driver_connected,
        "driver_stopped": driver_stopped,
        "movement_performed": False,
        "device_identity_persisted": False,
    }
    if error_stage is not None:
        evidence["error_stage"] = error_stage
    return evidence


def write_immutable_json(path: Path, payload: Mapping[str, Any]) -> str:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    digest = hashlib.sha256(encoded).hexdigest()
    if path.exists() and path.read_bytes() != encoded:
        raise FileExistsError(f"refusing to mutate existing evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return digest


def read_verified_json(path: Path, expected_sha256: str) -> dict[str, Any]:
    encoded = path.read_bytes()
    actual = hashlib.sha256(encoded).hexdigest()
    if actual != expected_sha256:
        raise ValueError("capability evidence hash mismatch")
    payload = json.loads(encoded)
    if not isinstance(payload, dict):
        raise ValueError("capability evidence root must be an object")
    return payload
