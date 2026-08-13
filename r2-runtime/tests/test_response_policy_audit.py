from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from r2_runtime.response_policy_audit import audit_response_policy, write_immutable_audit


PACKET = """
class Packet:
    class Flags:
        requests_response = 2
    class Manager:
        def new_packet(self, did, cid):
            flags = Packet.Flags.requests_response | Packet.Flags.is_activity
            return flags
"""
TOY = """
class Toy:
    def _execute(self, packet):
        self.__packet_queue.put(packet.build())
        return self._wait_packet(packet.id)
    def _wait_packet(self, key, timeout=10.0, check_error=False):
        return self.future.result(timeout)
"""
DRIVE = """
class Drive:
    _did = 22
    def set_raw_motors(toy, left_mode, left_speed, right_mode, right_speed, proc=None):
        toy._execute(Drive._encode(toy, 1, proc, [left_mode, left_speed, right_mode, right_speed]))
"""


class ResponsePolicyAuditTest(unittest.TestCase):
    def make_package(self, root: Path) -> Path:
        package = root / "spherov2"
        for relative, content in {
            "controls/v2.py": PACKET,
            "toy/__init__.py": TOY,
            "commands/drive.py": DRIVE,
        }.items():
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return package

    def test_static_audit_proves_client_wait_policy_without_hardware_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = audit_response_policy(
                self.make_package(Path(directory)), distribution_version="0.12.1"
            )
        self.assertEqual(
            payload["conclusion"], "client_requires_matching_response_for_raw_motor_command"
        )
        self.assertEqual(payload["firmware_behavior"], "unverified")
        self.assertEqual(payload["checks"]["wait_timeout_seconds"], 10.0)
        self.assertFalse(payload["movement_performed"])
        self.assertNotIn("package_root", json.dumps(payload))

    def test_version_source_drift_and_existing_output_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.make_package(root)
            with self.assertRaisesRegex(ValueError, "requires pinned"):
                audit_response_policy(package, distribution_version="0.12.0")
            (package / "toy/__init__.py").write_text("class Toy: pass", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing expected"):
                audit_response_policy(package, distribution_version="0.12.1")

            output = root / "audit.json"
            write_immutable_audit(output, {"safe": True})
            with self.assertRaises(FileExistsError):
                write_immutable_audit(output, {"safe": False})
