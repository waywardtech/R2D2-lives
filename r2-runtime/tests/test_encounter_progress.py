from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from r2_runtime.encounter_progress import DurableEncounterProgress, read_encounter_progress


class EncounterProgressTest(unittest.TestCase):
    def test_markers_are_durable_ordered_and_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.jsonl"
            recorder = DurableEncounterProgress(path)
            recorder.record("scan_started")
            recorder.record("scan_completed", {"droid_kind_count": 1})
            DurableEncounterProgress(path).record("connect_started")
            markers = read_encounter_progress(path)
            self.assertEqual([marker.sequence for marker in markers], [1, 2, 3])
            self.assertEqual(markers[-1].stage, "connect_started")

    def test_identity_and_exception_detail_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recorder = DurableEncounterProgress(Path(directory) / "progress.jsonl")
            for detail in ({"name": "private"}, {"address": "private"}, {"error": "secret"}):
                with self.subTest(detail=detail), self.assertRaisesRegex(ValueError, "unsafe"):
                    recorder.record("session_failed", detail)

    def test_tampered_sequence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.jsonl"
            path.write_text('{"detail":{},"sequence":2,"stage":"scan_started"}\n')
            with self.assertRaisesRegex(ValueError, "sequence"):
                read_encounter_progress(path)


if __name__ == "__main__":
    unittest.main()
