from pathlib import Path
import os
import subprocess
import sys
import unittest


class HardwareImportIsolationTest(unittest.TestCase):
    def test_hardware_modules_import_without_protocol_or_peer_source(self) -> None:
        project = Path(__file__).resolve().parents[1]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(project / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-S",
                "-c",
                (
                    "import r2_runtime.ble_owner; "
                    "import r2_runtime.capability_probe; "
                    "import r2_runtime.spherov2_backend"
                ),
            ],
            cwd=project,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
