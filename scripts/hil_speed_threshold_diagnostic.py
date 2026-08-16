"""One separately armed post-wake speed-threshold diagnostic pulse."""

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
from r2_runtime.hil_preflight import validate_speed_threshold_diagnostic_preflight
from r2_runtime.motion_watchdog import IndependentMotionWatchdog
from r2_runtime.recording import build_hil_failure_evidence, write_immutable_json
from r2_runtime.spherov2_backend import Spherov2LibraryBackend, StationaryProbePolicy

RAW_SPEED = 25
REQUESTED_WINDOW_S = 0.10
POST_WAKE_SETTLE_S = 3.0
WATCHDOG_TIMEOUT_S = 0.25


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One supervised R201 speed-threshold diagnostic")
    parser.add_argument("--authorize-speed-threshold-diagnostic", action="store_true")
    for flag in (
        "operator-present",
        "device-inspected",
        "temperature-ok",
        "keepout-clear",
        "emergency-stop-ready",
        "unplugged-from-charger",
        "physically-contained",
        "second-go-confirmed",
        "allow-wake-stance-cycle",
    ):
        parser.add_argument(f"--{flag}", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        preflight = validate_speed_threshold_diagnostic_preflight(args, os.environ)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    driver = Spherov2R2Driver(
        backend=Spherov2LibraryBackend(policy=StationaryProbePolicy(allow_wake_on_connect=True)),
        configured_identity=preflight.identity,
    )
    owner = BleOwner(driver)
    try:
        owner.connect_for_stationary_probe()
        time.sleep(POST_WAKE_SETTLE_S)
        watchdog = IndependentMotionWatchdog(driver.dispatch_emergency_stop)

        def pulse() -> None:
            owner.serialized(lambda: driver.dispatch_r2_drive_forward(RAW_SPEED))
            time.sleep(REQUESTED_WINDOW_S)

        result = watchdog.run(pulse, timeout_s=WATCHDOG_TIMEOUT_S)
        if result.terminal != "completed" or not result.stop_dispatched:
            raise RuntimeError("speed-threshold watchdog did not complete with an emergency stop")
        time.sleep(0.25)
        owner.disconnect("speed_threshold_diagnostic_complete")
    except Exception as error:
        try:
            driver.dispatch_emergency_stop()
        except Exception:
            pass
        try:
            owner.disconnect("speed_threshold_diagnostic_failed")
        except Exception:
            pass
        write_immutable_json(
            args.output,
            build_hil_failure_evidence(
                error_type=type(error).__name__,
                owner_state=owner.state.value,
                driver_connected=driver.connected,
                driver_stopped=driver.stopped,
            ),
        )
        raise SystemExit(2) from None
    evidence: dict[str, object] = {
        "schema_version": "1.0",
        "evidence_category": "hil_speed_threshold_diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "raw_speed": RAW_SPEED,
        "post_wake_settle_s": POST_WAKE_SETTLE_S,
        "requested_window_s": REQUESTED_WINDOW_S,
        "watchdog_timeout_s": WATCHDOG_TIMEOUT_S,
        "watchdog_terminal": result.terminal,
        "watchdog_elapsed_s": round(result.elapsed_s, 6),
        "stop_dispatch": "queued_unacknowledged",
        "measured_distance_m": None,
        "measurement_status": "operator_observation_required",
        "device_identity_persisted": False,
        "terminal": "disconnected_safe_hold",
    }
    payload = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    evidence["evidence_sha256"] = hashlib.sha256(payload).hexdigest()
    digest = write_immutable_json(args.output, evidence)
    print(
        json.dumps(
            {"report_sha256": digest, "requested_window_s": REQUESTED_WINDOW_S}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
