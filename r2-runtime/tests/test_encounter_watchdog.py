from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from r2_runtime.encounter_watchdog import (
    ENCOUNTER_WATCHDOG_ARM_TOKEN,
    supervise_encounter_process,
    validate_encounter_watchdog_authorization,
)


class EncounterWatchdogTest(unittest.TestCase):
    def test_hil_watchdog_refuses_by_default_before_child_start(self) -> None:
        with self.assertRaisesRegex(ValueError, "disabled without explicit authorization"):
            validate_encounter_watchdog_authorization(
                authorized=False, arm_token=None, timeout_s=40
            )

    def test_hil_watchdog_requires_exact_token_and_bounded_timeout(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact external"):
            validate_encounter_watchdog_authorization(
                authorized=True, arm_token="wrong", timeout_s=40
            )
        with self.assertRaisesRegex(ValueError, r"\[20, 120\]"):
            validate_encounter_watchdog_authorization(
                authorized=True,
                arm_token=ENCOUNTER_WATCHDOG_ARM_TOKEN,
                timeout_s=121,
            )
        validate_encounter_watchdog_authorization(
            authorized=True,
            arm_token=ENCOUNTER_WATCHDOG_ARM_TOKEN,
            timeout_s=40,
        )

    def test_normal_child_exit_does_not_create_timeout_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            evidence = temp / "watchdog.json"
            result = supervise_encounter_process(
                [sys.executable, "-c", "raise SystemExit(7)"],
                timeout_s=5,
                progress_path=temp / "progress.jsonl",
                watchdog_evidence_path=evidence,
            )
            self.assertFalse(result.timed_out)
            self.assertEqual(result.child_returncode, 7)
            self.assertFalse(evidence.exists())

    def test_timeout_terminates_child_and_writes_fail_closed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            evidence = temp / "watchdog.json"
            result = supervise_encounter_process(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                timeout_s=0.05,
                progress_path=temp / "progress.jsonl",
                watchdog_evidence_path=evidence,
                termination_grace_s=1,
            )
            payload = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertTrue(result.timed_out)
            self.assertEqual(payload["terminal"], "watchdog_timeout")
            self.assertEqual(payload["stall_classification"], "no_progress")
            self.assertTrue(payload["process_terminated"])
            self.assertFalse(payload["ble_disconnect_verified"])
            self.assertTrue(payload["operator_state_confirmation_required"])

    def test_existing_progress_or_evidence_refuses_before_child_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            progress = temp / "progress.jsonl"
            progress.write_text("reserved", encoding="utf-8")
            marker = temp / "child-ran"
            with self.assertRaises(FileExistsError):
                supervise_encounter_process(
                    [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"],
                    timeout_s=5,
                    progress_path=temp / "progress.jsonl",
                    watchdog_evidence_path=temp / "watchdog.json",
                    reserved_paths=(progress,),
                )
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
