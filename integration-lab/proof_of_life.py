"""Deterministic stationary proof-of-life simulation."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "r2-runtime" / "src"))

from r2_runtime.ble_owner import BleOwner  # noqa: E402
from r2_runtime.drivers import Spherov2R2Driver  # noqa: E402
from r2_runtime.proof_of_life import run_proof_of_life  # noqa: E402
from r2_runtime.sim_hardware import SimSpherov2Backend  # noqa: E402


def main() -> None:
    backend = SimSpherov2Backend()
    driver = Spherov2R2Driver(backend=backend, configured_identity="D2-SIMULATED")
    report = run_proof_of_life(
        BleOwner(driver),
        driver,
        seed=20260812,
        system_collector=lambda: {
            "schema_version": "1.0",
            "pi": {"hostname": "sim-pi", "state": "nominal"},
            "clock": {"synchronized": True},
            "issues": [],
            "overall": "nominal",
        },
    )
    payload = report.to_dict()
    payload["executed_primitives"] = backend.calls
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
