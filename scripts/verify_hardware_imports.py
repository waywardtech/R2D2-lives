"""Verify locked hardware imports on a Raspberry Pi without accessing BLE."""

from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT / "r2-runtime" / "src"))
sys.path.insert(0, os.fspath(ROOT / "protocol" / "src"))

from r2_runtime.hardware_import_check import verify_target_imports  # noqa: E402


def main() -> None:
    lock = ROOT / "r2-runtime" / "requirements-hardware-pi.lock"
    try:
        imported = verify_target_imports(lock)
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    print(f"target-Pi locked imports verified ({len(imported)} packages); BLE not accessed")


if __name__ == "__main__":
    main()
