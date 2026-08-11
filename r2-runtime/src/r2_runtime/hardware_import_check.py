"""Import-only verification for the locked Raspberry Pi hardware profile."""

from __future__ import annotations

from collections.abc import Callable
import importlib
from importlib import metadata
from pathlib import Path
import platform
import sys

from r2_runtime.hardware_lock import parse_lock

IMPORT_NAMES = {
    "bleak": "bleak",
    "dbus-fast": "dbus_fast",
    "numpy": "numpy",
    "spherov2": "spherov2",
    "transforms3d": "transforms3d",
    "typing-extensions": "typing_extensions",
}


def verify_target_imports(
    lock_path: Path,
    *,
    system: str | None = None,
    machine: str | None = None,
    python_version: tuple[int, int] | None = None,
    version_reader: Callable[[str], str] = metadata.version,
    importer: Callable[[str], object] = importlib.import_module,
) -> tuple[str, ...]:
    actual_system = system if system is not None else platform.system()
    actual_machine = machine if machine is not None else platform.machine()
    actual_python = python_version if python_version is not None else sys.version_info[:2]
    if actual_system != "Linux" or actual_machine.lower() not in {"aarch64", "arm64"}:
        raise RuntimeError("hardware import check requires Linux aarch64")
    if actual_python != (3, 11):
        raise RuntimeError("hardware import check requires Python 3.11")

    locked = parse_lock(lock_path)
    if set(locked) != set(IMPORT_NAMES):
        raise RuntimeError("hardware lock package set is not import-checkable")
    imported: list[str] = []
    for package in sorted(locked):
        expected_version = locked[package][0]
        actual_version = version_reader(package)
        if actual_version != expected_version:
            raise RuntimeError(
                f"locked version mismatch for {package}: "
                f"expected {expected_version}, got {actual_version}"
            )
        importer(IMPORT_NAMES[package])
        imported.append(package)
    return tuple(imported)
