"""Verify the target-Pi hardware lock and, optionally, an offline wheelhouse."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "r2-runtime" / "requirements-hardware-pi.lock"
DEFAULT_MANIFEST = ROOT / "r2-runtime" / "hardware-wheelhouse.manifest.json"
sys.path.insert(0, os.fspath(ROOT / "r2-runtime" / "src"))

from r2_runtime.hardware_lock import verify_metadata, verify_wheelhouse  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--wheelhouse", type=Path)
    args = parser.parse_args()
    manifest = verify_metadata(args.lock, args.manifest)
    if args.wheelhouse is not None:
        verify_wheelhouse(manifest, args.wheelhouse)
    suffix = " and wheelhouse" if args.wheelhouse is not None else ""
    print(f"target-Pi hardware lock{suffix} verified ({len(manifest['artifacts'])} wheels)")


if __name__ == "__main__":
    main()
