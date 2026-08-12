"""Pi-only launcher that selects the externally configured R2 exactly."""

from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "encounter-live.json"
STAGED_SITE_PACKAGES = ROOT / "site-packages"
sys.path.insert(0, os.fspath(ROOT / "r2-runtime" / "src"))
sys.path.insert(0, os.fspath(STAGED_SITE_PACKAGES))

from r2_runtime.discovery_policy import select_configured_toy


def main() -> None:
    configured_identity = os.environ.get("R2_DEVICE_IDENTITY", "")
    if not configured_identity:
        raise SystemExit("R2_DEVICE_IDENTITY must be configured outside source control")
    scanner = import_module("spherov2.scanner")
    r2_type = import_module("spherov2.toy.r2d2").R2D2
    toys = scanner.find_toys(timeout=8, toy_types=(r2_type,))
    try:
        select_configured_toy(toys, configured_identity)
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error)) from None
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
