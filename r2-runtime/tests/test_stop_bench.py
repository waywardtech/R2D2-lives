from __future__ import annotations

import unittest

from r2_runtime.ble_owner import BleOwner, ConnectionState
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.sim_hardware import SimSpherov2Backend
from r2_runtime.stop_bench import run_stop_bench_session


class StopBenchSessionTest(unittest.TestCase):
    def run_with(self, backend: SimSpherov2Backend):
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        result = run_stop_bench_session(owner, driver)
        self.assertEqual(owner.state, ConnectionState.OFFLINE)
        self.assertTrue(owner.stopped)
        self.assertFalse(driver.connected)
        return result

    def test_normal_session_uses_one_stop_and_disconnect(self) -> None:
        backend = SimSpherov2Backend()
        result = self.run_with(backend)
        self.assertIsNone(result.error_type)
        self.assertEqual(result.battery_state, "ok")
        self.assertEqual(backend.calls.count("stop"), 1)
        self.assertEqual(backend.calls[-2:], ["stop", "disconnect"])

    def test_stop_timeout_is_returned_without_retry(self) -> None:
        class TimeoutBackend(SimSpherov2Backend):
            def stop(self) -> None:
                self.calls.append("stop_timeout")
                raise TimeoutError("injected response timeout")

        backend = TimeoutBackend()
        result = self.run_with(backend)
        self.assertEqual(result.error_type, "TimeoutError")
        self.assertEqual(backend.calls.count("stop_timeout"), 1)
        self.assertEqual(backend.calls[-1], "disconnect")

    def test_unsafe_battery_still_disconnects_once_and_remains_invalid(self) -> None:
        class UnsafeBatteryBackend(SimSpherov2Backend):
            def battery(self) -> dict[str, object]:
                self.calls.append("battery")
                return {"state": "critical", "voltage_v": 3.0}

        backend = UnsafeBatteryBackend()
        result = self.run_with(backend)
        self.assertEqual(result.error_type, "UnsafeBatteryState")
        self.assertEqual(result.battery_state, "critical")
        self.assertEqual(backend.calls.count("stop"), 1)

    def test_battery_query_failure_still_disconnects_once(self) -> None:
        class BatteryFailureBackend(SimSpherov2Backend):
            def battery(self) -> dict[str, object]:
                self.calls.append("battery_failure")
                raise OSError("injected query failure")

        backend = BatteryFailureBackend()
        result = self.run_with(backend)
        self.assertEqual(result.error_type, "OSError")
        self.assertEqual(result.battery_state, "unobserved")
        self.assertEqual(backend.calls.count("stop"), 1)
        self.assertEqual(backend.calls[-1], "disconnect")


if __name__ == "__main__":
    unittest.main()
