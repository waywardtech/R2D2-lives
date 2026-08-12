from __future__ import annotations

import unittest

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.proof_of_life import run_proof_of_life
from r2_runtime.sim_hardware import SimSpherov2Backend


class ProofOfLifeTest(unittest.TestCase):
    def test_simulation_reports_all_primitives_and_safe_final_state(self) -> None:
        backend = SimSpherov2Backend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        stages: list[str] = []
        report = run_proof_of_life(
            BleOwner(driver),
            driver,
            seed=42,
            system_collector=lambda: {
                "schema_version": "1.0",
                "pi": {"hostname": "sim-pi"},
                "clock": {"synchronized": True},
                "issues": [],
                "overall": "nominal",
            },
            stage_sink=lambda stage, _detail: stages.append(stage),
        )
        payload = report.to_dict()
        self.assertFalse(payload["movement_performed"])
        self.assertEqual(payload["final_state"], "offline")
        self.assertTrue(driver.stopped)
        self.assertTrue(any(call.startswith("audio:") for call in backend.calls))
        self.assertTrue(any(call.startswith("head:") for call in backend.calls))
        self.assertTrue(any(call == "led:8" for call in backend.calls))
        self.assertEqual(payload["status"]["droid"]["expression"]["status"], "completed")
        self.assertEqual(
            stages,
            [
                "system_status_collected",
                "connect_started",
                "connect_completed",
                "identity_checked",
                "battery_checked",
                "head_checked",
                "expression_started",
                "expression_completed",
                "disconnect_started",
                "disconnect_completed",
                "session_completed",
            ],
        )

    def test_unsafe_battery_blocks_expression_and_disconnects(self) -> None:
        class UnsafeBackend(SimSpherov2Backend):
            def battery(self) -> dict[str, object]:
                return {"state": "critical", "voltage_v": 3.1, "provenance": "simulation"}

        backend = UnsafeBackend()
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        with self.assertRaisesRegex(PermissionError, "blocks proof of life"):
            run_proof_of_life(
                BleOwner(driver),
                driver,
                seed=42,
                system_collector=lambda: {"pi": {}, "clock": {}, "issues": []},
            )
        self.assertFalse(any(call.startswith("expression:") for call in backend.calls))
        self.assertFalse(driver.connected)
        self.assertTrue(driver.stopped)


if __name__ == "__main__":
    unittest.main()
