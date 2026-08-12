from __future__ import annotations

from pathlib import Path
import runpy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "scripts" / "hil_launch_single_r2_encounter.py"


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


if __name__ == "__main__":
    unittest.main()
