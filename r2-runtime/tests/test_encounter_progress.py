from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from r2_runtime.encounter_progress import (
    DurableEncounterProgress,
    EncounterProgressMarker,
    build_encounter_watchdog_evidence,
    classify_encounter_stall,
    read_encounter_progress,
    validate_encounter_progress,
)


def markers(*stages: tuple[str, dict[str, object]]) -> tuple[EncounterProgressMarker, ...]:
    return tuple(
        EncounterProgressMarker(sequence, stage, detail)
        for sequence, (stage, detail) in enumerate(stages, 1)
    )


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

    def test_stage_specific_detail_types_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            recorder = DurableEncounterProgress(Path(directory) / "progress.jsonl")
            invalid = (
                ("scan_started", {"battery_safe": True}),
                ("scan_completed", {"droid_kind_count": True}),
                ("battery_checked", {"battery_safe": "yes"}),
                ("expression_started", {"reaction_number": 0}),
            )
            for stage, detail in invalid:
                with self.subTest(stage=stage), self.assertRaisesRegex(ValueError, "detail"):
                    recorder.record(stage, detail)

    def test_invalid_transition_and_reaction_order_are_rejected(self) -> None:
        invalid_sequences = (
            markers(("connect_started", {})),
            markers(("scan_started", {}), ("connect_started", {})),
            markers(
                ("scan_started", {}),
                ("scan_completed", {"droid_kind_count": 1}),
                ("connect_started", {}),
                ("connect_completed", {}),
                ("battery_checked", {"battery_safe": True}),
                ("expression_started", {"reaction_number": 1}),
                ("expression_completed", {"reaction_number": 2}),
            ),
        )
        for sequence in invalid_sequences:
            with self.subTest(sequence=sequence), self.assertRaises(ValueError):
                validate_encounter_progress(sequence)

    def test_recorder_rejects_invalid_transition_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.jsonl"
            recorder = DurableEncounterProgress(path)
            recorder.record("scan_started")
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "transition"):
                recorder.record("connect_started")
            self.assertEqual(path.read_bytes(), before)

    def test_each_watchdog_boundary_has_a_stable_classification(self) -> None:
        prefix = [
            ("scan_started", {}),
            ("scan_completed", {"droid_kind_count": 1}),
            ("connect_started", {}),
            ("connect_completed", {}),
            ("battery_checked", {"battery_safe": True}),
            ("expression_started", {"reaction_number": 1}),
            ("expression_completed", {"reaction_number": 1}),
            ("disconnect_started", {}),
            ("disconnect_completed", {}),
            ("session_completed", {}),
        ]
        expected = (
            "scan_stalled",
            "connection_start_stalled",
            "connection_stalled",
            "battery_query_stalled",
            "expression_planning_stalled",
            "expression_execution_stalled",
            "expression_loop_or_cleanup_stalled",
            "disconnect_stalled",
            "final_report_stalled",
            "completed",
        )
        self.assertEqual(classify_encounter_stall(()), "no_progress")
        for length, classification in enumerate(expected, 1):
            with self.subTest(stage=prefix[length - 1][0]):
                self.assertEqual(
                    classify_encounter_stall(markers(*prefix[:length])), classification
                )

    def test_failed_cleanup_boundary_is_distinguished(self) -> None:
        sequence = markers(
            ("scan_started", {}),
            ("scan_completed", {"droid_kind_count": 1}),
            ("connect_started", {}),
            ("session_failed", {}),
            ("disconnect_started", {}),
            ("disconnect_completed", {}),
        )
        self.assertEqual(classify_encounter_stall(sequence[:4]), "disconnect_start_stalled")
        self.assertEqual(classify_encounter_stall(sequence), "failure_report_stalled")

    def test_no_droid_and_unsafe_battery_boundaries_are_distinguished(self) -> None:
        no_droid = markers(("scan_started", {}), ("scan_completed", {"droid_kind_count": 0}))
        unsafe_battery = markers(
            ("scan_started", {}),
            ("scan_completed", {"droid_kind_count": 1}),
            ("connect_started", {}),
            ("connect_completed", {}),
            ("battery_checked", {"battery_safe": False}),
        )
        self.assertEqual(classify_encounter_stall(no_droid), "finalization_stalled")
        self.assertEqual(classify_encounter_stall(unsafe_battery), "failure_recording_stalled")

    def test_watchdog_evidence_is_deterministic_and_identity_free(self) -> None:
        sequence = markers(
            ("scan_started", {}),
            ("scan_completed", {"droid_kind_count": 1}),
            ("connect_started", {}),
        )
        first = build_encounter_watchdog_evidence(sequence)
        second = build_encounter_watchdog_evidence(sequence)
        self.assertEqual(first, second)
        self.assertEqual(first["stall_classification"], "connection_stalled")
        self.assertEqual(first["journal_integrity"], "verified")
        serialized = str(first).lower()
        for forbidden in ("address", "exception", "audio", "semantic", "private"):
            self.assertNotIn(forbidden, serialized)

    def test_absent_journal_is_reported_without_claiming_integrity(self) -> None:
        report = build_encounter_watchdog_evidence((), journal_present=False)
        self.assertEqual(report["stall_classification"], "no_progress")
        self.assertEqual(report["journal_integrity"], "absent")


if __name__ == "__main__":
    unittest.main()
