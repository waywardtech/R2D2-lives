"""Pi-only launcher that discovers exactly one R2 before arming one proof-of-life child."""

from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "proof-of-life-live.json"
STAGED_SITE_PACKAGES = ROOT / "site-packages"
sys.path.insert(0, os.fspath(STAGED_SITE_PACKAGES))


def main() -> None:
    scanner = import_module("spherov2.scanner")
    r2_type = import_module("spherov2.toy.r2d2").R2D2
    toys = scanner.find_toys(timeout=8, toy_types=(r2_type,))
    if len(toys) != 1:
        raise SystemExit(f"expected exactly one R2-D2 advertisement; observed {len(toys)}")
    os.environ["R2_DEVICE_IDENTITY"] = toys[0].name
    os.environ["R2_PROOF_OF_LIFE_ARM_TOKEN"] = "AUTHORIZE_STATIONARY_PROOF_OF_LIFE"
    os.environ["R2_PROOF_OF_LIFE_PROGRESS_PATH"] = os.fspath(ROOT / "proof-of-life-progress.jsonl")
    sys.argv = [
        "hil_proof_of_life.py",
        "--authorize-proof-of-life",
        "--operator-present",
        "--device-inspected",
        "--temperature-ok",
        "--keepout-clear",
        "--emergency-stop-ready",
        "--charging-safe-only",
        "--second-go-confirmed",
        "--output",
        os.fspath(OUTPUT),
    ]
    runpy.run_path(os.fspath(ROOT / "scripts" / "hil_proof_of_life.py"), run_name="__main__")


if __name__ == "__main__":
    main()
