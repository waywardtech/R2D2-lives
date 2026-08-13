# R2 Runtime scaffold

Phase 0 supplies simulation-only adapters. The Phase 1 stationary-probe slice
adds an unavailable-by-default `Spherov2R2Driver` boundary, serialized owner,
capability report, and record/replay support. `SimDroidDriver` records safe-hold
state and never addresses BLE. `NullSpatialProviderClient` and
`SimSpatialProviderClient` are chosen by the `R2_SPATIAL_PROVIDER` configuration
value. Real hardware access is unavailable by default and must be separately
armed and supervised. See `hardware-provenance.toml` for the declared
0.12.1 baseline and checked resolver evidence.

The optional Raspberry Pi hardware profile is hash-locked in
`requirements-hardware-pi.lock`. Verify an offline wheelhouse with
`python ../scripts/verify_hardware_lock.py --wheelhouse <directory>` before any
target installation. This does not authorize BLE access or physical movement.
On the Pi, `python ../scripts/verify_hardware_imports.py` performs a versioned,
import-only check and refuses non-Linux/aarch64 hosts before importing anything.

The non-actuating iPhone dashboard lives under `webapp/R2D2` and is deployed by
Apache at `/R2D2/`. Its loopback chat service has bounded local continuity and
no hardware command endpoint. See `../docs/proof-of-life-and-dashboard.md`.
Real proof-of-life execution remains a separately armed HIL operation.
