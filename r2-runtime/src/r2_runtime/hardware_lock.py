"""Validation for the target-Pi dependency lock and offline wheelhouse."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

LOCK_LINE = re.compile(
    r"^(?P<package>[A-Za-z0-9_.-]+)==(?P<version>[^\s]+) "
    r"--hash=sha256:(?P<sha256>[0-9a-f]{64})$"
)
FORBIDDEN_WINDOWS_TOKENS = ("bleak-winrt", "win32", "win_amd64")


def canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def parse_lock(path: Path) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = LOCK_LINE.fullmatch(line)
        if match is None:
            raise ValueError(f"invalid lock line {number}: {line}")
        name = canonical_name(match.group("package"))
        if name in entries:
            raise ValueError(f"duplicate locked package: {name}")
        entries[name] = (match.group("version"), match.group("sha256"))
    if not entries:
        raise ValueError("hardware lock is empty")
    return entries


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("hardware manifest root must be an object")
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported hardware manifest schema")
    target = manifest.get("target", {})
    expected = {
        "implementation": "cp",
        "python_version": "3.11",
        "abi": "cp311",
        "platform": "manylinux2014_aarch64",
        "operating_system": "Linux",
    }
    if target != expected:
        raise ValueError(f"unexpected hardware target: {target}")
    return manifest


def verify_metadata(lock_path: Path, manifest_path: Path) -> dict[str, Any]:
    locked = parse_lock(lock_path)
    manifest = load_manifest(manifest_path)
    required = {canonical_name(name) for name in manifest["required_packages"]}
    artifacts: dict[str, dict[str, Any]] = {}
    for artifact in manifest["artifacts"]:
        name = canonical_name(artifact["package"])
        if name in artifacts:
            raise ValueError(f"duplicate manifest package: {name}")
        filename = artifact["filename"].lower()
        if any(token in name or token in filename for token in FORBIDDEN_WINDOWS_TOKENS):
            raise ValueError(f"Windows-only artifact forbidden in Pi manifest: {filename}")
        artifacts[name] = artifact
    if set(locked) != required or set(artifacts) != required:
        raise ValueError("lock, manifest artifacts, and required package set differ")
    for name, (version, digest) in locked.items():
        artifact = artifacts[name]
        if artifact["version"] != version or artifact["sha256"] != digest:
            raise ValueError(f"lock and manifest differ for {name}")
        if not artifact["filename"].endswith(".whl") or artifact["size"] <= 0:
            raise ValueError(f"invalid wheel metadata for {name}")
    return manifest


def verify_wheelhouse(manifest: dict[str, Any], wheelhouse: Path) -> None:
    for artifact in manifest["artifacts"]:
        wheel = wheelhouse / artifact["filename"]
        if not wheel.is_file():
            raise ValueError(f"missing wheel: {wheel.name}")
        if wheel.stat().st_size != artifact["size"]:
            raise ValueError(f"size mismatch: {wheel.name}")
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if digest != artifact["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {wheel.name}")
