"""Pi-only launcher that keeps the single discovered R2 identity in memory."""

from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "encounter-live.json"


def main() -> None:
    scanner = import_module("spherov2.scanner")
    r2_type = import_module("spherov2.toy.r2d2").R2D2
    toys = scanner.find_toys(timeout=8, toy_types=(r2_type,))
    if len(toys) != 1:
        raise SystemExit(f"expected exactly one R2-D2 advertisement; observed {len(toys)}")
    os.environ["R2_DEVICE_IDENTITY"] = toys[0].name
    os.environ["R2_ENCOUNTER_ARM_TOKEN"] = "AUTHORIZE_STATIONARY_HEAD_AUDIO"
    os.environ["R2_ENCOUNTER_PROGRESS_PATH"] = os.fspath(ROOT / "encounter-progress.jsonl")
    sys.argv = [
        "hil_stationary_droid_encounter.py",
        "--authorize-stationary-encounter",
        "--operator-present",
        "--device-inspected",
        "--temperature-ok",
        "--keepout-clear",
        "--emergency-stop-ready",
        "--charging-safe-only",
        "--second-go-confirmed",
        "--max-reactions",
        "3",
        "--output",
        os.fspath(OUTPUT),
    ]
    runpy.run_path(
        os.fspath(ROOT / "scripts" / "hil_stationary_droid_encounter.py"),
        run_name="__main__",
    )


if __name__ == "__main__":
    main()
