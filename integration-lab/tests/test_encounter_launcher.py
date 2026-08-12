from __future__ import annotations

from pathlib import Path
import os
import runpy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "hil_launch_single_r2_encounter.py"
PROOF_LAUNCHER = ROOT / "scripts" / "hil_launch_proof_of_life.py"


class EncounterLauncherTest(unittest.TestCase):
    def test_launcher_adds_isolated_hardware_dependencies_before_main(self) -> None:
        original_path = list(sys.path)
        try:
            namespace = runpy.run_path(str(LAUNCHER), run_name="encounter_launcher_test")
            expected = ROOT / "site-packages"
            self.assertEqual(namespace["STAGED_SITE_PACKAGES"], expected)
            self.assertEqual(Path(sys.path[0]), expected)
        finally:
            sys.path[:] = original_path

    def test_proof_launcher_adds_isolated_hardware_dependencies_before_main(self) -> None:
        original_path = list(sys.path)
        try:
            namespace = runpy.run_path(str(PROOF_LAUNCHER), run_name="proof_launcher_test")
            expected = ROOT / "site-packages"
            self.assertEqual(namespace["STAGED_SITE_PACKAGES"], expected)
            self.assertEqual(Path(sys.path[0]), expected)
        finally:
            sys.path[:] = original_path

    def test_launchers_require_external_identity_before_live_scanning(self) -> None:
        original = os.environ.pop("R2_DEVICE_IDENTITY", None)
        try:
            for launcher in (LAUNCHER, PROOF_LAUNCHER):
                namespace = runpy.run_path(str(launcher), run_name="identity_gate_test")
                with self.assertRaisesRegex(SystemExit, "configured outside source control"):
                    namespace["main"]()
        finally:
            if original is not None:
                os.environ["R2_DEVICE_IDENTITY"] = original


if __name__ == "__main__":
    unittest.main()
