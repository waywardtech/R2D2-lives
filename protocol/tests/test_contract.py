from __future__ import annotations

import json
from pathlib import Path
import unittest

from sap_protocol.generated import CommandRequest, EventEnvelope, Pose
from sap_protocol.json_schema import SchemaValidator
from sap_protocol.validation import ValidationError

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "specs" / "contracts" / "examples"


class ContractExamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        schema_path = ROOT / "protocol" / "schema" / "sap-common.schema.json"
        cls.validator = SchemaValidator(json.loads(schema_path.read_text(encoding="utf-8")))

    def _load(self, name: str) -> dict:
        return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))

    def test_pose_event_example_round_trips_and_preserves_measurement_semantics(self) -> None:
        source = self._load("pose-event.json")
        event = EventEnvelope.from_dict(source)
        pose = Pose.from_dict(event.payload["pose"])
        self.assertEqual(event.to_dict(), source)
        self.assertEqual(pose.frame_id, "urn:sap:frame:agent:r2-d2-01:odom")
        self.assertEqual(event.clock.uncertainty_ms, 2.5)
        self.assertEqual(event.monotonic_ns, 9_912_345_678)

    def test_probe_command_example_is_valid(self) -> None:
        command = CommandRequest.from_dict(self._load("probe-command.json"))
        self.assertEqual(command.type, "emit_acoustic_probe")
        self.assertEqual(command.parameters["gain_normalized"], 0.2)

    def test_invalid_fixture_missing_clock_is_rejected(self) -> None:
        invalid = self._load("pose-event.json")
        del invalid["clock"]
        with self.assertRaisesRegex(ValidationError, "missing required fields"):
            EventEnvelope.from_dict(invalid)

    def test_invalid_fixture_non_normalized_quaternion_is_rejected(self) -> None:
        invalid = self._load("pose-event.json")
        invalid["payload"]["pose"]["orientation"]["w"] = 2.0
        with self.assertRaisesRegex(ValidationError, "normalized"):
            Pose.from_dict(invalid["payload"]["pose"])

    def test_unknown_additive_event_fields_are_tolerated_and_preserved(self) -> None:
        source = self._load("pose-event.json")
        source["future_field"] = {"safe": True}
        parsed = EventEnvelope.from_dict(source)
        self.assertEqual(parsed.to_dict()["future_field"], {"safe": True})

    def test_all_canonical_examples_pass_their_declared_json_schema(self) -> None:
        for schema_path in sorted(EXAMPLES.glob("*.schema.json")):
            wrapper = json.loads(schema_path.read_text(encoding="utf-8"))
            instance_path = schema_path.with_name(
                schema_path.name.removesuffix(".schema.json") + ".json"
            )
            with self.subTest(example=instance_path.name):
                self.validator.validate(self._load(instance_path.name), wrapper)

    def test_invalid_variants_fail_schema_validation(self) -> None:
        cases = []
        capabilities = self._load("agent-capabilities.json")
        capabilities["role"] = "motor_controller"
        cases.append((capabilities, "Capabilities"))
        command = self._load("probe-command.json")
        command["parameters"]["waveform_sha256"] = "not-a-hash"
        cases.append((command, "CommandRequest"))
        event = self._load("pose-event.json")
        event["clock"]["uncertainty_ms"] = -1
        cases.append((event, "EventEnvelope"))
        advisory = self._load("route-advisory.json")
        advisory["confidence"] = 1.5
        cases.append((advisory, "RouteAdvisory"))
        for instance, definition in cases:
            with self.subTest(definition=definition), self.assertRaises(ValidationError):
                self.validator.validate(instance, {"$ref": f"#/$defs/{definition}"})

    def test_schema_reference_to_scalar_is_rejected(self) -> None:
        validator = SchemaValidator({"$defs": {"invalid": "not-an-object"}})
        with self.assertRaisesRegex(ValidationError, "reference is not an object"):
            validator.validate({}, {"$ref": "#/$defs/invalid"})


if __name__ == "__main__":
    unittest.main()
