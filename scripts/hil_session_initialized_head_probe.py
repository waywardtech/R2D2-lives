"""One separately authorized no-drive R201 session-initialized head probe."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.hil_preflight import validate_stationary_preflight
from r2_runtime.recording import build_hil_failure_evidence, write_immutable_json
from r2_runtime.spherov2_backend import Spherov2LibraryBackend, StationaryProbePolicy


def main() -> None:
    parser = argparse.ArgumentParser(description="One no-drive session-initialized R201 head probe")
    parser.add_argument("--authorize-stationary-hil", action="store_true")
    for flag in (
        "operator-present",
        "device-inspected",
        "temperature-ok",
        "keepout-clear",
        "emergency-stop-ready",
    ):
        parser.add_argument(f"--{flag}", action="store_true")
    parser.add_argument("--allow-wake-on-connect", action="store_true")
    parser.add_argument("--allow-audio-preview", action="store_true")
    parser.add_argument("--audio-id", type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        identity = validate_stationary_preflight(args, os.environ)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    backend = Spherov2LibraryBackend(
        policy=StationaryProbePolicy(
            allow_wake_on_connect=args.allow_wake_on_connect,
            allow_session_initialized_head_read=True,
        )
    )
    driver = Spherov2R2Driver(backend=backend, configured_identity=identity)
    owner = BleOwner(driver)
    try:
        owner.connect_for_stationary_probe()
        detail = owner.serialized(
            lambda: backend.exercise_stationary("head.session_initialized_read")
        )
        driver.safe_hold()
        owner.disconnect("session_initialized_head_probe_complete")
    except Exception as error:
        try:
            driver.dispatch_emergency_stop()
        except Exception:
            pass
        try:
            owner.disconnect("session_initialized_head_probe_failed")
        except Exception:
            pass
        write_immutable_json(
            args.output,
            build_hil_failure_evidence(
                error_type=type(error).__name__,
                owner_state=owner.state.value,
                driver_connected=driver.connected,
                driver_stopped=driver.stopped,
                error_stage="session_initialized_head_read",
            ),
        )
        raise SystemExit(2) from None
    evidence = {
        "schema_version": "1.0",
        "evidence_category": "hil_session_initialized_head_probe",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "session_setup": "wake_neutral_sensor_streams",
        "head_query": detail,
        "movement_performed": False,
        "terminal": "disconnected_safe_hold",
        "device_identity_persisted": False,
    }
    digest = write_immutable_json(args.output, evidence)
    print(json.dumps({"report_sha256": digest, "terminal": evidence["terminal"]}))


if __name__ == "__main__":
    main()
