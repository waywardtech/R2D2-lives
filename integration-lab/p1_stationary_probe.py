"""Phase 1 simulation evidence: five cycles and a virtual 30-minute soak."""

from __future__ import annotations

import json

from r2_runtime.ble_owner import BleOwner
from r2_runtime.capability_probe import StationaryCapabilityProbe
from r2_runtime.drivers import Spherov2R2Driver
from r2_runtime.sim_hardware import SimSpherov2Backend

SEED = 20260811


def run() -> dict[str, object]:
    cycle_hashes: list[str] = []
    for cycle in range(5):
        backend = SimSpherov2Backend(seed=SEED + cycle)
        driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
        report = StationaryCapabilityProbe(BleOwner(driver), driver).run(
            generated_at=f"2030-01-01T00:00:0{cycle}Z"
        )
        assert report.final_state == "safe_hold"
        assert not report.movement_performed
        assert backend.calls[-2:] == ["stop", "disconnect"]
        cycle_hashes.append(report.sha256())

    # Virtual-time soak exercises a stationary health sample once per minute.
    soak_backend = SimSpherov2Backend(seed=SEED)
    soak_driver = Spherov2R2Driver(backend=soak_backend, configured_identity="D2-SIMULATED")
    soak_owner = BleOwner(soak_driver)
    soak_owner.connect_for_stationary_probe()
    samples = []
    try:
        for minute in range(31):
            battery = soak_owner.serialized(soak_backend.battery)
            samples.append({"virtual_elapsed_s": minute * 60, "battery": battery})
    finally:
        soak_owner.disconnect("virtual_30_minute_soak_complete")
    assert soak_owner.stopped
    return {
        "seed": SEED,
        "evidence_category": "simulation",
        "connect_probe_disconnect_cycles": 5,
        "cycle_report_sha256": cycle_hashes,
        "virtual_soak_duration_s": 1800,
        "virtual_soak_samples": len(samples),
        "movement_performed": False,
        "final_state": "safe_hold",
        "hil_gate_satisfied": False,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
