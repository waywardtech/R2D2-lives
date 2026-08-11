# Workspace changelog

## Unreleased

- Begin Phase 1 with a simulation/replay-first stationary capability probe.
- Add the single serialized BLE-owner lifecycle, fail-closed 0.12.1 adapter
  boundary, privacy-preserving capability reports, immutable evidence, five
  simulated cycles, and a virtual 30-minute stationary soak.
- Add a separately marked HIL command that remains disabled before device access.
- Verify the upstream 0.12.1 source hash/license, select Bleak 0.21.1 for the
  Python 3.11 compatibility baseline, and add the lazy real-library adapter.
- Gate LED/head/audio operations independently, exclude MAC addresses, restore
  preview state, and block optional actions on unsafe battery state.
- Add a six-wheel, SHA-256-locked CPython 3.11 Linux/aarch64 hardware profile,
  artifact manifest, offline verifier, and Windows-package rejection tests.
- Add a target-only import/version checker that refuses the wrong platform and
  never scans BLE or constructs the hardware backend.
- Verify all six locked packages offline on the Debian 13/aarch64 target host
  under Python 3.11.2 without BLE access.

## 0.1.0 - 2026-08-11

- Scaffold independent SAP, R2 Runtime, BSM, and Integration Lab projects.
- Add reproducible dependency-free SAP boundary types and client protocol.
- Add contract validation, adapter selection, cross-import/standalone checks,
  and a seeded simulation-only command/session/event round trip.
- Establish stable Make/Python task entry points and Phase 0 operator guidance.
