"""Content-addressed capability evidence recording and replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


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
    return json.loads(encoded)

