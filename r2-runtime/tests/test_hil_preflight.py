from argparse import Namespace
import unittest

from r2_runtime.hil_preflight import validate_stationary_preflight, validate_stop_bench_preflight


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


def bench_arguments(**overrides: object) -> Namespace:
    values = {
        "authorize_stop_response_bench": False,
        "operator_present": False,
        "device_inspected": False,
        "temperature_ok": False,
        "keepout_clear": False,
        "emergency_stop_ready": False,
        "unplugged_from_charger": False,
        "physically_contained": False,
        "second_go_confirmed": False,
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

    def test_stop_bench_is_disabled_without_exact_second_gate(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact stop-response authorization"):
            validate_stop_bench_preflight(bench_arguments(), {})
        with self.assertRaisesRegex(ValueError, "unplugged-from-charger.*second-go-confirmed"):
            validate_stop_bench_preflight(
                bench_arguments(
                    authorize_stop_response_bench=True,
                    operator_present=True,
                    device_inspected=True,
                    temperature_ok=True,
                    keepout_clear=True,
                    emergency_stop_ready=True,
                ),
                {},
            )

    def test_stop_bench_requires_external_arm_clock_and_identity(self) -> None:
        args = bench_arguments(**{name: True for name in (
            "authorize_stop_response_bench", "operator_present", "device_inspected",
            "temperature_ok", "keepout_clear", "emergency_stop_ready",
            "unplugged_from_charger", "physically_contained", "second_go_confirmed",
        )})
        environment = {
            "R2_DEVICE_IDENTITY": "private",
            "R2_STOP_BENCH_ARM_TOKEN": "AUTHORIZE_ONE_RAW_MOTOR_OFF",
            "R2_CLOCK_SYNC_SOURCE": "ntp",
            "R2_CLOCK_UNCERTAINTY_MS": "2.5",
        }
        result = validate_stop_bench_preflight(args, environment)
        self.assertEqual(result.identity, "private")
        self.assertEqual(result.clock_uncertainty_ms, 2.5)
        for key in environment:
            if key == "R2_STOP_BENCH_ARM_TOKEN":
                broken = dict(environment)
                broken[key] = "wrong"
                with self.assertRaisesRegex(ValueError, "external arm token"):
                    validate_stop_bench_preflight(args, broken)


if __name__ == "__main__":
    unittest.main()
