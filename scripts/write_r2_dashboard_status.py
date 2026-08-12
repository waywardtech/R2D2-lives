"""Write an atomic, privacy-safe status snapshot consumed by the static PWA."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.system_status import collect_system_status, merge_droid_snapshot  # noqa: E402


def _latest_droid(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        status = payload.get("status", {})
        droid = status.get("droid")
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
        return None
    return dict(droid) if isinstance(droid, dict) else None


def write_snapshot(output: Path, droid_evidence: Path | None = None) -> None:
    payload = merge_droid_snapshot(collect_system_status(), _latest_droid(droid_evidence))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--droid-evidence", type=Path)
    args = parser.parse_args()
    write_snapshot(args.output, args.droid_evidence)


if __name__ == "__main__":
    main()
