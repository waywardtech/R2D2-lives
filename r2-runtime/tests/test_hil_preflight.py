from argparse import Namespace
import unittest

from r2_runtime.hil_preflight import validate_stationary_preflight


def arguments(**overrides: object) -> Namespace:
    values = {
        "authorize_stationary_hil": False,
        "operator_present": False,
        "device_inspected": False,
        "temperature_ok": False,
        "keepout_clear": False,
        "emergency_stop_ready": False,
        "allow_audio_preview": False,
        "audio_id": None,
    }
    values.update(overrides)
    return Namespace(**values)


class HilPreflightTest(unittest.TestCase):
    def test_default_refuses_before_identity_or_backend_is_needed(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit stationary authorization"):
            validate_stationary_preflight(arguments(), {})

    def test_every_physical_preflight_condition_is_required(self) -> None:
        args = arguments(authorize_stationary_hil=True)
        with self.assertRaisesRegex(ValueError, "operator-present.*emergency-stop-ready"):
            validate_stationary_preflight(args, {"R2_DEVICE_IDENTITY": "private"})

    def test_identity_stays_external(self) -> None:
        args = arguments(
            authorize_stationary_hil=True,
            operator_present=True,
            device_inspected=True,
            temperature_ok=True,
            keepout_clear=True,
            emergency_stop_ready=True,
        )
        self.assertEqual(
            validate_stationary_preflight(args, {"R2_DEVICE_IDENTITY": "private"}), "private"
        )

    def test_audio_requires_explicit_verified_id(self) -> None:
        args = arguments(
            authorize_stationary_hil=True,
            operator_present=True,
            device_inspected=True,
            temperature_ok=True,
            keepout_clear=True,
            emergency_stop_ready=True,
            allow_audio_preview=True,
        )
        with self.assertRaisesRegex(ValueError, "verified --audio-id"):
            validate_stationary_preflight(args, {"R2_DEVICE_IDENTITY": "private"})


if __name__ == "__main__":
    unittest.main()
