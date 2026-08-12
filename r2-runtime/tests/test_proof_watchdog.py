from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from r2_runtime.proof_watchdog import (
    PROOF_WATCHDOG_ARM_TOKEN,
    supervise_proof_process,
    validate_proof_watchdog_authorization,
)


class ProofWatchdogTest(unittest.TestCase):
    def test_authorization_and_timeout_are_bounded(self) -> None:
        with self.assertRaisesRegex(ValueError, "disabled"):
            validate_proof_watchdog_authorization(authorized=False, arm_token=None, timeout_s=75)
        with self.assertRaisesRegex(ValueError, "exact external"):
            validate_proof_watchdog_authorization(authorized=True, arm_token="wrong", timeout_s=75)
        validate_proof_watchdog_authorization(
            authorized=True, arm_token=PROOF_WATCHDOG_ARM_TOKEN, timeout_s=75
        )

    def test_timeout_classifies_last_stage_and_terminates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            progress = root / "progress.jsonl"
            evidence = root / "watchdog.json"
            journal = (
                '{"detail":{},"occurred_at":"2030-01-01T00:00:00Z","sequence":1,"stage":"system_status_collected"}\n'
                '{"detail":{},"occurred_at":"2030-01-01T00:00:01Z","sequence":2,"stage":"connect_started"}\n'
            )
            result = supervise_proof_process(
                [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; import time; Path({str(progress)!r}).write_text({journal!r}); time.sleep(10)",
                ],
                timeout_s=0.5,
                progress_path=progress,
                watchdog_evidence_path=evidence,
                termination_grace_s=1,
            )
            payload = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertTrue(result.timed_out)
            self.assertEqual(payload["stall_classification"], "connection_stalled")
            self.assertFalse(payload["ble_disconnect_verified"])
            self.assertFalse(payload["movement_performed"])

    def test_existing_artifact_refuses_before_child_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reserved = root / "live.json"
            reserved.write_text("reserved", encoding="utf-8")
            marker = root / "child-ran"
            with self.assertRaises(FileExistsError):
                supervise_proof_process(
                    [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"],
                    timeout_s=1,
                    progress_path=root / "progress.jsonl",
                    watchdog_evidence_path=root / "watchdog.json",
                    reserved_paths=(reserved,),
                )
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
