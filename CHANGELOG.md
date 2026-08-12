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
- Record a read-only Pi readiness audit with the Bluetooth controller left off;
  distinguish Pi CPU temperature from ambient and droid sensor evidence.
- Characterize the first stationary-HIL discovery attempt: Pi rfkill recovery
  succeeded, R2 did not advertise, and no droid connection or command occurred.
- Load top-level R2 Runtime exports lazily so the hardware adapter can be tested
  without importing SAP or simulation application modules.
- Verify bounded discovery distinguishes one in-scope R2-D2 from one out-of-scope
  BB-8 without connecting either or persisting advertised identity.
- Fix HIL stop-timeout cleanup so stop is attempted once and BLE always closes;
  use deterministic raw motor OFF/0 without changing heading.
- Persist stop-timeout HIL evidence with a failed capability and
  `disconnected_stop_unconfirmed` terminal state instead of claiming success.
- Persist sanitized immutable failure evidence for earlier probe exceptions,
  excluding exception text, configured identity, and device addresses.
- Add the first immutable real-R201 HIL report and enforce its SHA-256 during
  documentation checks; the stop-timeout cycle remains a failed gate result.
- Record operator confirmation that R2 returned to normal after the optional
  watchdog and prohibit further charging-state retries.
- Document the upstream response-policy mismatch and block motion HIL rather
  than treating a transmitted, unacknowledged stop packet as success.
- Add a deterministic, privacy-safe BLE-owner lifecycle recorder and strict
  replay validator whose failures cannot interrupt stop/disconnect processing.
- Add a reviewed stationary lifecycle fixture and reject movement, clock/sequence
  tampering, invalid state transitions, external reason data, and unknown fields.
- Add a non-executing R201 stop-response bench procedure with a one-command limit,
  privacy-safe metadata capture, physical shutdown prerequisite, fail-closed
  result classification, and no-retry cleanup.
- Add a simulation-only stop-response metadata recorder/classifier that accepts
  only one DID 22/CID 1 transmission, hashes and discards packet bytes, correlates
  one response, restricts decoded errors, and never promotes timeout to success.
- Add an opt-in traced raw-motor-OFF executor over the pinned vendor encode/execute
  seam while leaving the normal public stop path and packet semantics unchanged.
- Add a separately marked stop-response runner that refuses by default and
  requires external arming, complete off-charger containment/clock preflight,
  no retry, zero residual BLE connections, and post-test physical confirmation.
- Preserve an operator-confirmed response timeout as `stop_unconfirmed` while
  keeping unsafe battery, missing confirmation, and unrelated errors invalid.
- Extract bench-session orchestration into R2 Runtime and cover normal, timeout,
  unsafe-battery, and query-failure paths with one-stop/no-retry assertions.
- Add least-privilege Python 3.11 GitHub Actions simulation CI and a static guard
  rejecting HIL, hardware identities, Bluetooth/SSH/sudo, and self-hosted runners.
- Update the root README to distinguish simulation-default automation from the
  separate disabled-by-default local R201 hardware profile.
- Remove an unnecessary pip cache after the first hosted run failed in post-job
  cleanup, and update checkout/setup-python to their Node 24 action releases.
- Verify the corrected GitHub Actions simulation workflow passes on the hosted
  Python 3.11 runner with hardware-capable paths statically excluded.
- Pin checkout and setup-python actions to immutable commits resolved from their
  official v6 tags, and reject floating action tags in the CI safety guard.
- Add an offline tracked-file scan for secret/private-key formats, BLE/device
  identities, forbidden credential files, and locked dependency license coverage.
- Add a cross-platform SHA-256-locked Ruff/mypy toolchain and require formatting,
  lint, and strict typing in local checks and hosted CI; harden typed JSON roots.
- Add privacy-safe nearby-droid classification and a chat-guided deterministic
  stationary expression compiler using bounded R2 head, LED, and stock sound
  primitives; exclude unverified full animations and add a separately armed HIL run.
- Add a Pi-only, single-R2 in-memory identity launcher; record the first live
  encounter as indeterminate after watchdog expiry and controller-level cleanup.
- Add append-only, fsynced, privacy-safe encounter stage markers so watchdog
  termination preserves the last completed scan/connect/battery/expression/cleanup stage.
- Validate encounter journals as legal state-machine prefixes and convert a
  watchdog-truncated or absent journal into immutable, deterministic,
  identity-free stall evidence without promoting it to a passing HIL cycle.
- Add a separately armed external HIL watchdog that refuses reused evidence,
  bounds and terminates one fixed encounter child, automatically classifies a
  timeout, and never equates process termination with verified BLE cleanup.
- Make the Pi-only launcher load the verified isolated hardware dependency
  directory itself rather than relying on an operator-supplied `PYTHONPATH`.
- Preserve the first failing stationary-expression phase across restoration,
  include that stable phase in sanitized HIL evidence, and close a failed BLE
  transport without waiting on another response-dependent motor-OFF command.

## 0.1.0 - 2026-08-11

- Scaffold independent SAP, R2 Runtime, BSM, and Integration Lab projects.
- Add reproducible dependency-free SAP boundary types and client protocol.
- Add contract validation, adapter selection, cross-import/standalone checks,
  and a seeded simulation-only command/session/event round trip.
- Establish stable Make/Python task entry points and Phase 0 operator guidance.
