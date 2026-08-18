"""Validate the evidence-gated delivery register without accessing hardware."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_ENTRY_KEYS = frozenset(
    {
        "id",
        "scope",
        "state",
        "hypothesis",
        "baseline",
        "measurement",
        "decision_rule",
        "sources",
        "next_action",
    }
)
VALID_STATES = frozenset({"proposed", "active", "completed_benefit", "completed_no_benefit"})
VALID_SOURCE_KINDS = frozenset({"official", "upstream", "community"})


def validate_register(payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("benefit register must be an object")
    if payload.get("schema_version") != "1.0":
        raise ValueError("benefit register schema_version must be 1.0")
    if not isinstance(payload.get("policy"), str) or "measurable benefit" not in payload["policy"]:
        raise ValueError("benefit register must state the measurable-benefit policy")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("benefit register requires at least one entry")
    ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or REQUIRED_ENTRY_KEYS - entry.keys():
            raise ValueError("benefit register entry is missing required fields")
        identifier = entry["id"]
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("benefit register IDs must be unique non-empty strings")
        ids.add(identifier)
        if entry["state"] not in VALID_STATES:
            raise ValueError("benefit register state is invalid")
        measurement = entry["measurement"]
        if not isinstance(measurement, dict) or not all(
            isinstance(measurement.get(key), str) and measurement[key]
            for key in ("metric", "unit", "threshold", "collection")
        ):
            raise ValueError("benefit register measurement is incomplete")
        baseline = entry["baseline"]
        if not isinstance(baseline, dict) or not isinstance(baseline.get("evidence"), list):
            raise ValueError("benefit register baseline evidence is incomplete")
        sources = entry["sources"]
        if not isinstance(sources, list) or not sources:
            raise ValueError("benefit register requires at least one source")
        for source in sources:
            if (
                not isinstance(source, dict)
                or source.get("kind") not in VALID_SOURCE_KINDS
                or not isinstance(source.get("url"), str)
                or not source["url"].startswith("https://")
            ):
                raise ValueError("benefit register source is invalid")
        if entry["state"].startswith("completed") and not isinstance(entry.get("result"), str):
            raise ValueError("completed benefit register entries require a result")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", type=Path, default=Path("planning/benefit-register.json"))
    args = parser.parse_args()
    validate_register(json.loads(args.register.read_text(encoding="utf-8")))
    print("evidence-gated delivery register verified")


if __name__ == "__main__":
    main()
