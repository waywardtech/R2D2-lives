# Phase 0 operator notes

## User-visible behavior

Phase 0 is a simulation-only contract foundation. The R2 scaffold starts with a
simulated droid in `safe_hold` and selects the null spatial provider unless
`R2_SPATIAL_PROVIDER=sim` is set. BSM selects only its generic seeded simulator.
No BLE, microphone, network, acoustic-probe, charging, or real-motion path is
present.

## Commands

On systems with GNU Make, use `make bootstrap`, `make check`, `make contract`,
`make sim-smoke`, `make test`, and `make docs-check`. On Windows without Make,
run the equivalent `python scripts/tasks.py <task>` command.

The simulation smoke prints the fixed seed, SAP identifiers, simulation clock
quality, duplicate-suppression result, and final `safe_hold` state. A failed or
stale command also ends in `safe_hold` and reports a stable SAP reason code.

## Observability and failure mode

Every simulated terminal command produces one ordered event carrying session,
correlation, causation, UTC, monotonic, clock-source, and uncertainty fields.
Unknown additive event fields survive parsing and serialization. Session or
capability incompatibility is rejected before command execution.

## Rollback

Phase 0 has no migrations, persistent state, or external deployment. Rollback
is removal of the scaffold files. No physical device state needs recovery.

## Safety classification

Evidence is automated contract testing and deterministic simulation only. It is
not HIL, bench, real-room, or evidence of physical safety or acoustic accuracy.
Real R2 movement remains unauthorized.

