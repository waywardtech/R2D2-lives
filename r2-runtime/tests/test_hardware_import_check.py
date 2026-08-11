from pathlib import Path
import tempfile
import unittest

from r2_runtime.hardware_import_check import verify_target_imports


LOCK = """\
bleak==0.21.1 --hash=sha256:{hash}
dbus-fast==2.46.4 --hash=sha256:{hash}
numpy==1.26.4 --hash=sha256:{hash}
spherov2==0.12.1 --hash=sha256:{hash}
transforms3d==0.4.1 --hash=sha256:{hash}
typing-extensions==4.16.0 --hash=sha256:{hash}
""".format(hash="0" * 64)


class HardwareImportCheckTest(unittest.TestCase):
    def test_wrong_host_refuses_before_import(self) -> None:
        imported: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "hardware.lock"
            lock.write_text(LOCK, encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Linux aarch64"):
                verify_target_imports(
                    lock,
                    system="Windows",
                    machine="AMD64",
                    python_version=(3, 11),
                    importer=lambda name: imported.append(name),
                )
        self.assertEqual(imported, [])

    def test_exact_versions_are_imported_without_backend_construction(self) -> None:
        versions = {
            "bleak": "0.21.1",
            "dbus-fast": "2.46.4",
            "numpy": "1.26.4",
            "spherov2": "0.12.1",
            "transforms3d": "0.4.1",
            "typing-extensions": "4.16.0",
        }
        imported: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "hardware.lock"
            lock.write_text(LOCK, encoding="utf-8")
            result = verify_target_imports(
                lock,
                system="Linux",
                machine="aarch64",
                python_version=(3, 11),
                version_reader=versions.__getitem__,
                importer=lambda name: imported.append(name),
            )
        self.assertEqual(len(result), 6)
        self.assertEqual(len(imported), 6)


if __name__ == "__main__":
    unittest.main()
