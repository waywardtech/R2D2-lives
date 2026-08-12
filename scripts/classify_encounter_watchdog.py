"""Convert a durable encounter journal into immutable sanitized timeout evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.encounter_progress import (  # noqa: E402
    build_encounter_watchdog_evidence,
    read_encounter_progress,
)
from r2_runtime.recording import write_immutable_json  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify a timed-out stationary encounter")
    parser.add_argument("--progress", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    present = args.progress.is_file()
    markers = read_encounter_progress(args.progress) if present else ()
    payload = build_encounter_watchdog_evidence(markers, journal_present=present)
    digest = write_immutable_json(args.output, payload)
    print(
        json.dumps(
            {
                "report_sha256": digest,
                "stall_classification": payload["stall_classification"],
                "terminal": payload["terminal"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
