"""One separately armed post-wake R201 raw-drive diagnostic.

This follows a failed immediate-post-wake pulse.  It waits for the visible
stance transition to settle before one fixed low-speed diagnostic pulse, and
keeps all actuation behind a fresh authorization and independent OFF/0 watchdog.
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
from r2_runtime.hil_preflight import validate_post_wake_motion_diagnostic_preflight
from r2_runtime.motion_watchdog import IndependentMotionWatchdog
from r2_runtime.recording import build_hil_failure_evidence, write_immutable_json
from r2_runtime.spherov2_backend import Spherov2LibraryBackend, StationaryProbePolicy

RAW_SPEED = 10
REQUESTED_WINDOW_S = 0.10
POST_WAKE_SETTLE_S = 3.0
WATCHDOG_TIMEOUT_S = 0.25


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One supervised post-wake R201 drive diagnostic")
    parser.add_argument("--authorize-post-wake-motion-diagnostic", action="store_true")
    parser.add_argument("--operator-present", action="store_true")
    parser.add_argument("--device-inspected", action="store_true")
    parser.add_argument("--temperature-ok", action="store_true")
    parser.add_argument("--keepout-clear", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--unplugged-from-charger", action="store_true")
    parser.add_argument("--physically-contained", action="store_true")
    parser.add_argument("--second-go-confirmed", action="store_true")
    parser.add_argument("--allow-wake-stance-cycle", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _success_evidence(terminal: str, elapsed_s: float) -> dict[str, object]:
    evidence: dict[str, object] = {
        "schema_version": "1.0",
        "evidence_category": "hil_post_wake_motion_diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "raw_speed": RAW_SPEED,
        "post_wake_settle_s": POST_WAKE_SETTLE_S,
        "requested_window_s": REQUESTED_WINDOW_S,
        "watchdog_timeout_s": WATCHDOG_TIMEOUT_S,
        "watchdog_terminal": terminal,
        "watchdog_elapsed_s": round(elapsed_s, 6),
        "stop_dispatch": "queued_unacknowledged",
        "measured_distance_m": None,
        "measurement_status": "operator_observation_required",
        "device_identity_persisted": False,
        "terminal": "disconnected_safe_hold",
    }
    payload = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
    evidence["evidence_sha256"] = hashlib.sha256(payload).hexdigest()
    return evidence


def main() -> None:
    args = build_parser().parse_args()
    try:
        preflight = validate_post_wake_motion_diagnostic_preflight(args, os.environ)
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
            owner.serialized(lambda: driver.dispatch_bounded_forward(RAW_SPEED))
            time.sleep(REQUESTED_WINDOW_S)

        result = watchdog.run(pulse, timeout_s=WATCHDOG_TIMEOUT_S)
        if result.terminal != "completed" or not result.stop_dispatched:
            raise RuntimeError(
                "post-wake diagnostic watchdog did not complete with an emergency stop"
            )
        time.sleep(0.25)
        owner.disconnect("post_wake_motion_diagnostic_complete")
    except Exception as error:
        try:
            driver.dispatch_emergency_stop()
        except Exception:
            pass
        try:
            owner.disconnect("post_wake_motion_diagnostic_failed")
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
    digest = write_immutable_json(args.output, _success_evidence(result.terminal, result.elapsed_s))
    print(
        json.dumps(
            {"report_sha256": digest, "requested_window_s": REQUESTED_WINDOW_S}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
