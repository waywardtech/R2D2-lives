"""One separately armed, no-response-wait OFF/0 dispatch bench.

This confirms only that the reviewed packet is queued and BLE closes cleanly.
It is not a movement test and does not claim physical braking effectiveness.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.hil_preflight import validate_nonblocking_stop_bench_preflight
from r2_runtime.recording import build_hil_failure_evidence, write_immutable_json
from r2_runtime.spherov2_backend import Spherov2LibraryBackend


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Single nonblocking R201 OFF/0 dispatch bench")
    parser.add_argument("--authorize-nonblocking-stop-bench", action="store_true")
    parser.add_argument("--operator-present", action="store_true")
    parser.add_argument("--device-inspected", action="store_true")
    parser.add_argument("--temperature-ok", action="store_true")
    parser.add_argument("--keepout-clear", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--unplugged-from-charger", action="store_true")
    parser.add_argument("--physically-contained", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _success_evidence() -> dict[str, object]:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    evidence: dict[str, object] = {
        "schema_version": "1.0",
        "evidence_category": "hil_nonblocking_stop_dispatch",
        "generated_at": timestamp,
        "stop_dispatch": "queued_unacknowledged",
        "movement_performed": False,
        "device_identity_persisted": False,
        "terminal": "disconnected_safe_hold",
    }
    payload = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    evidence["evidence_sha256"] = hashlib.sha256(payload).hexdigest()
    return evidence


def main() -> None:
    args = build_parser().parse_args()
    try:
        preflight = validate_nonblocking_stop_bench_preflight(args, os.environ)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    driver = Spherov2R2Driver(
        backend=Spherov2LibraryBackend(), configured_identity=preflight.identity
    )
    owner = BleOwner(driver)
    try:
        owner.connect_for_stationary_probe()
        owner.serialized(driver.dispatch_emergency_stop)
        # Let the pinned sender write the queued packet. This is not a response wait.
        time.sleep(0.25)
        owner.disconnect("nonblocking_stop_dispatch_complete")
    except Exception as error:
        try:
            owner.disconnect("nonblocking_stop_dispatch_failed")
        except Exception:
            pass
        failure = build_hil_failure_evidence(
            error_type=type(error).__name__,
            owner_state=owner.state.value,
            driver_connected=driver.connected,
            driver_stopped=driver.stopped,
        )
        write_immutable_json(args.output, failure)
        raise SystemExit(2) from None
    digest = write_immutable_json(args.output, _success_evidence())
    print(json.dumps({"movement_performed": False, "report_sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
