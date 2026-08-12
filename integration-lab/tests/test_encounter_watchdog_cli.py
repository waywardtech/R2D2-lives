from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class EncounterWatchdogCliTest(unittest.TestCase):
    def test_cli_writes_immutable_sanitized_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            progress = temp / "progress.jsonl"
            output = temp / "evidence.json"
            progress.write_text(
                '{"detail":{},"sequence":1,"stage":"scan_started"}\n', encoding="utf-8"
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT / "r2-runtime" / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "classify_encounter_watchdog.py"),
                    "--progress",
                    str(progress),
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            summary = json.loads(result.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["stall_classification"], "scan_stalled")
            self.assertEqual(
                summary["report_sha256"], hashlib.sha256(output.read_bytes()).hexdigest()
            )
            progress.write_text(
                "".join(
                    (
                        '{"detail":{},"sequence":1,"stage":"scan_started"}\n',
                        '{"detail":{"droid_kind_count":1},"sequence":2,"stage":"scan_completed"}\n',
                    )
                ),
                encoding="utf-8",
            )
            with self.assertRaises(subprocess.CalledProcessError):
                subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "classify_encounter_watchdog.py"),
                        "--progress",
                        str(progress),
                        "--output",
                        str(output),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env,
                )


if __name__ == "__main__":
    unittest.main()
