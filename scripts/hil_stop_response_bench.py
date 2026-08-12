"""Explicitly armed, stationary R201 raw-motor-OFF response bench.

This command is disabled by default, sends no non-zero motor value, never retries,
and requires post-disconnect physical confirmation before valid classification.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.hil_preflight import validate_stop_bench_preflight
from r2_runtime.packet_trace import (
    StopResponseTraceRecorder,
    classify_stop_response_trace,
    physical_state_for_trace,
)
from r2_runtime.recording import build_hil_failure_evidence, write_immutable_json
from r2_runtime.session_recording import SessionClock
from r2_runtime.spherov2_backend import Spherov2LibraryBackend, TracedRawMotorOffExecutor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ONE stationary R201 raw-motor-OFF response trace")
    parser.add_argument("--authorize-stop-response-bench", action="store_true")
    parser.add_argument("--operator-present", action="store_true")
    parser.add_argument("--device-inspected", action="store_true")
    parser.add_argument("--temperature-ok", action="store_true")
    parser.add_argument("--keepout-clear", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--unplugged-from-charger", action="store_true")
    parser.add_argument("--physically-contained", action="store_true")
    parser.add_argument("--second-go-confirmed", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _clock_id() -> str:
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip().replace("-", "")
    if len(boot_id) != 32 or any(character not in "0123456789abcdef" for character in boot_id):
        raise RuntimeError("opaque boot clock identity unavailable")
    return "clock-" + boot_id


def _connected_device_count() -> int:
    result = subprocess.run(
        ["bluetoothctl", "devices", "Connected"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        return 1
    return sum(1 for line in result.stdout.splitlines() if line.startswith("Device "))


def main() -> None:
    args = build_parser().parse_args()
    try:
        preflight = validate_stop_bench_preflight(args, os.environ)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    recorder = StopResponseTraceRecorder(
        session_ref="session-" + secrets.token_hex(16),
        clock=SessionClock(
            _clock_id(), preflight.clock_sync_source, preflight.clock_uncertainty_ms
        ),
        evidence_category="HIL-stationary",
    )
    backend = Spherov2LibraryBackend(stop_executor=TracedRawMotorOffExecutor(recorder))
    driver = Spherov2R2Driver(backend=backend, configured_identity=preflight.identity)
    owner = BleOwner(driver)
    error_type: str | None = None
    try:
        owner.connect_for_stationary_probe()
        battery = owner.serialized(backend.battery)
        if str(battery.get("state", "unknown")).lower() not in {"ok", "charged", "not_charging"}:
            error_type = "UnsafeBatteryState"
    except Exception as error:
        error_type = type(error).__name__
    finally:
        if driver.connected:
            try:
                owner.disconnect("stationary_probe_complete")
            except Exception as error:
                error_type = error_type or type(error).__name__

    if recorder.observation_count == 0:
        failure = build_hil_failure_evidence(
            error_type=error_type or "NoStopObservation",
            owner_state=owner.state.value,
            driver_connected=driver.connected,
            driver_stopped=driver.stopped,
        )
        digest = write_immutable_json(args.output, failure)
        print(json.dumps({"terminal": "failed", "report_sha256": digest}, sort_keys=True))
        raise SystemExit(2)

    print("R2 is disconnected. Verify normal physical state and zero unexpected wheel activity.", flush=True)
    confirmation = input("Type PHYSICAL_NORMAL exactly to finalize: ").strip()
    payload = recorder.finalize(
        owner_state=owner.state.value,
        ble_connections=_connected_device_count(),
        physical_state=physical_state_for_trace(
            operator_confirmed=confirmation == "PHYSICAL_NORMAL",
            error_type=error_type,
        ),
    )
    classification = classify_stop_response_trace(payload)
    digest = write_immutable_json(args.output, payload)
    print(json.dumps({"classification": classification, "report_sha256": digest, "error_type": error_type}, sort_keys=True))
    if classification != "acknowledged_success":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
