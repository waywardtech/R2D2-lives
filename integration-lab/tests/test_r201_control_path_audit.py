from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "audit_r201_control_path", ROOT / "scripts" / "audit_r201_control_path.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class R201ControlPathAuditTest(unittest.TestCase):
    def test_reports_the_stock_default_and_diagnostic_secondary_difference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "toy").mkdir()
            (root / "commands").mkdir()
            (root / "toy" / "r2d2.py").write_text(
                "generic_raw_motor = Drive.generic_raw_motor\n", encoding="utf-8"
            )
            (root / "toy" / "bb9e.py").write_text(
                "set_raw_motors = Drive.set_raw_motors\ndrive_with_heading = Drive.drive_with_heading\n",
                encoding="utf-8",
            )
            (root / "commands" / "drive.py").write_text(
                "\n".join(
                    (
                        "def set_raw_motors(toy, left_mode: RawMotorModes, left_speed, right_mode: RawMotorModes, right_speed, proc=None):",
                        "def drive_with_heading(toy, speed, heading, drive_flags: DriveFlags, proc=None):",
                        "def generic_raw_motor(toy, index: GenericRawMotorIndexes, mode: GenericRawMotorModes, speed, proc=None):",
                    )
                ),
                encoding="utf-8",
            )
            backend = root / "spherov2_backend.py"
            backend.write_text("processors.Processors.SECONDARY\n" * 3, encoding="utf-8")
            result = MODULE.audit(root, backend)
        self.assertFalse(result["hardware_accessed"])
        self.assertEqual(result["control_path_differences_count"], 2)
        self.assertEqual(result["upstream_stock_r2_drive_processor"], "default_primary")

    def test_fails_closed_when_upstream_binding_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "toy").mkdir()
            (root / "commands").mkdir()
            for path in (
                root / "toy" / "r2d2.py",
                root / "toy" / "bb9e.py",
                root / "commands" / "drive.py",
            ):
                path.write_text("", encoding="utf-8")
            backend = root / "spherov2_backend.py"
            backend.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pinned source drift"):
                MODULE.audit(root, backend)


if __name__ == "__main__":
    unittest.main()
