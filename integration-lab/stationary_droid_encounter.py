"""Deterministic stationary R2/nearby-droid spectator scenario."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.ble_owner import BleOwner
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.encounter_session import run_droid_encounter_session
from r2_runtime.encounters import DroidEncounterChat
from r2_runtime.sim_hardware import SimSpherov2Backend


def main() -> None:
    backend = SimSpherov2Backend(nearby_droids=("bb8",))
    driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
    report = run_droid_encounter_session(
        BleOwner(driver), driver, DroidEncounterChat(seed=20260811), max_reactions=3
    )
    payload = report.to_dict()
    payload["seed"] = 20260811
    payload["executed_primitives"] = tuple(
        call for call in backend.calls if call.startswith(("audio:", "head:", "expression:"))
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
