import json
from pathlib import Path
import tempfile
import unittest

from r2_runtime.hardware_lock import load_manifest, parse_lock, verify_metadata

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = PROJECT / "requirements-hardware-pi.lock"
DEFAULT_MANIFEST = PROJECT / "hardware-wheelhouse.manifest.json"


class HardwareLockTest(unittest.TestCase):
    def test_checked_lock_and_manifest_match(self) -> None:
        manifest = verify_metadata(DEFAULT_LOCK, DEFAULT_MANIFEST)
        self.assertEqual(len(manifest["artifacts"]), 6)
        self.assertIn("dbus-fast", parse_lock(DEFAULT_LOCK))

    def test_windows_artifact_is_rejected(self) -> None:
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        manifest["artifacts"][0]["filename"] = "bleak-winrt-1.2.0.whl"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Windows-only artifact"):
                verify_metadata(DEFAULT_LOCK, path)

    def test_unhashed_lock_line_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.lock"
            path.write_text("bleak==0.21.1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid lock line"):
                parse_lock(path)

    def test_non_object_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "root must be an object"):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
