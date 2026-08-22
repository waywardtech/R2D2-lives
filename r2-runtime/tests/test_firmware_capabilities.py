from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError

from r2_runtime.firmware_capabilities import load_capability_profile, profile_sha256

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "r2-runtime" / "capabilities" / "r201-firmware-7.0.101.json"


class FirmwareCapabilityProfileTest(unittest.TestCase):
    def test_actual_profile_is_private_identity_free_and_evidence_backed(self) -> None:
        profile = load_capability_profile(PROFILE)
        self.assertTrue(profile.gate_p1_complete)
        self.assertEqual(profile.capabilities["wake.stance_cycle"].state, "verified")
        self.assertEqual(profile.capabilities["led.dome_logic_display"].state, "verified")
        head = profile.capabilities["head.position_read"]
        self.assertEqual(head.state, "verified")
        self.assertEqual(
            head.evidence,
            ("evidence/hil/session-head-b25bec4-20260820T210421Z.json",),
        )
        audio = profile.capabilities["audio.quiet_preview"]
        self.assertEqual(audio.state, "verified")
        self.assertEqual(
            audio.evidence,
            (
                "evidence/hil/session-audio-c93d04d-20260820T213520Z.json",
                "evidence/hil/session-audio-c93d04d-operator-observation.json",
            ),
        )
        self.assertEqual(profile.capabilities["drive.bounded_calibration"].state, "verified")
        self.assertEqual(profile.capabilities["emergency_stop.physical"].state, "verified")
        self.assertEqual(profile.capabilities["stop.physical_effectiveness"].state, "verified")
        self.assertNotIn("D2-", PROFILE.read_text(encoding="utf-8"))
        for capability in profile.capabilities.values():
            for evidence in (*capability.evidence, *capability.supersedes):
                self.assertTrue(evidence.startswith(("evidence/hil/", "docs/")), evidence)
                self.assertNotIn("..", Path(evidence).parts)
                if (ROOT / ".git").exists():
                    self.assertTrue((ROOT / evidence).is_file(), evidence)
        self.assertEqual(len(profile_sha256(PROFILE)), 64)

    def test_gate_cannot_complete_with_untested_physical_controls(self) -> None:
        payload = json.loads(PROFILE.read_text(encoding="utf-8"))
        payload["gate_p1_complete"] = True
        payload["capabilities"]["stop.physical_effectiveness"]["state"] = "untested"
        with tempfile.TemporaryDirectory() as raw_temp:
            path = Path(raw_temp) / "invalid.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "physical motion gate"):
                load_capability_profile(path)

    def test_terminal_state_requires_evidence(self) -> None:
        payload = json.loads(PROFILE.read_text(encoding="utf-8"))
        payload["capabilities"]["wake.stance_cycle"]["evidence"] = []
        with tempfile.TemporaryDirectory() as raw_temp:
            path = Path(raw_temp) / "invalid.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "requires evidence"):
                load_capability_profile(path)


if __name__ == "__main__":
    unittest.main()
