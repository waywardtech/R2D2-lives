from __future__ import annotations

import unittest

from r2_runtime.ble_owner import BleOwner, ConnectionState
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.encounter_session import run_droid_encounter_session
from r2_runtime.encounters import DroidEncounterChat
from r2_runtime.sim_hardware import SimSpherov2Backend


class DroidEncounterSessionTest(unittest.TestCase):
    def make_session(
        self, nearby_droids: tuple[str, ...] = ("bb8",)
    ) -> tuple[SimSpherov2Backend, Spherov2R2Driver, BleOwner]:
        backend = SimSpherov2Backend(nearby_droids=nearby_droids)
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        return backend, driver, BleOwner(driver)

    def test_nearby_bb8_triggers_bounded_stationary_reactions(self) -> None:
        backend, driver, owner = self.make_session()
        report = run_droid_encounter_session(
            owner, driver, DroidEncounterChat(seed=11), max_reactions=3
        )
        self.assertEqual(report.observed_droid_kinds, ("bb8",))
        self.assertEqual(len(report.reactions), 3)
        self.assertFalse(report.movement_performed)
        self.assertFalse(report.device_identity_persisted)
        self.assertEqual(report.final_state, "offline")
        self.assertEqual(owner.state, ConnectionState.OFFLINE)
        self.assertTrue(driver.stopped)
        self.assertNotIn("drive", " ".join(backend.calls))
        self.assertEqual(backend.calls[-2:], ["stop", "disconnect"])
        self.assertEqual(backend.calls.count("expression_restored"), 3)

    def test_no_other_droid_does_not_connect_or_react(self) -> None:
        backend, driver, owner = self.make_session(())
        report = run_droid_encounter_session(owner, driver, DroidEncounterChat())
        self.assertEqual(report.observed_droid_kinds, ())
        self.assertEqual(report.reactions, ())
        self.assertEqual(backend.calls, ["discover_nearby_droids"])

    def test_unsafe_battery_blocks_every_expression_and_disconnects(self) -> None:
        class CriticalBackend(SimSpherov2Backend):
            def battery(self) -> dict[str, object]:
                self.calls.append("battery")
                return {"state": "critical", "voltage_v": 3.0}

        backend = CriticalBackend(nearby_droids=("bb8",))
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        owner = BleOwner(driver)
        with self.assertRaisesRegex(PermissionError, "critical"):
            run_droid_encounter_session(owner, driver, DroidEncounterChat())
        self.assertFalse(any(call.startswith("expression:") for call in backend.calls))
        self.assertEqual(backend.calls[-2:], ["stop", "disconnect"])
        self.assertEqual(owner.state, ConnectionState.OFFLINE)

    def test_reaction_limit_is_bounded(self) -> None:
        backend, driver, owner = self.make_session()
        with self.assertRaisesRegex(ValueError, "\[1, 5\]"):
            run_droid_encounter_session(owner, driver, DroidEncounterChat(), max_reactions=6)
        self.assertEqual(backend.calls, [])

    def test_progress_identifies_every_completed_stage_without_identity(self) -> None:
        backend, driver, owner = self.make_session()
        markers: list[tuple[str, dict[str, object]]] = []
        run_droid_encounter_session(
            owner,
            driver,
            DroidEncounterChat(),
            max_reactions=2,
            stage_sink=lambda stage, detail: markers.append((stage, dict(detail))),
        )
        self.assertEqual(
            [stage for stage, _ in markers],
            [
                "scan_started",
                "scan_completed",
                "connect_started",
                "connect_completed",
                "battery_checked",
                "expression_started",
                "expression_completed",
                "expression_started",
                "expression_completed",
                "disconnect_started",
                "disconnect_completed",
                "session_completed",
            ],
        )
        self.assertNotIn("identity", str(markers).lower())


if __name__ == "__main__":
    unittest.main()
