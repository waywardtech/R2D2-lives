# Project status

Last updated: 2026-08-11  
Current phase: Phase 0  
Gate state: PASS

## Current objective

Deliver the Phase 0 contract/workspace foundation and collect automated and
simulation evidence for Gate P0.

## Requirement/evidence status

| Requirement/gate item | State | Evidence/command/artifact | Notes |
|---|---|---|---|
| ARCH-001 / standalone products | pass | `python scripts/tasks.py check` | Both isolated suites pass with peer absent |
| SAP-001, SAP-003, SAP-005 | pass | protocol and integration tests | Session, clock, command lifecycle |
| SAP-002, SAP-004 | pass | contract fixtures and sim smoke | SI/named-frame/pose uncertainty preserved |
| SAP-006, SAP-007 | pass | duplicate/cursor/additive-field tests | Ordered resume and forward compatibility |
| ARCH-003 / provider selection | pass | R2 scaffold tests | Null and Sim configuration |
| ARCH-004 / agent selection | pass | BSM scaffold tests | Generic SimMobileAgent only |
| TEST-001, TEST-003 | pass | simulation fault tests | No hardware path; final safe state asserted |
| Gate P0 | pass | `python scripts/tasks.py test`, `sim-smoke`, `docs-check` | Automated/contract/simulation evidence complete |

Evidence category: automated, contract, simulation.

## Completed this phase

- Specification pack checksum verified and source-of-truth copied under `specs/`.
- Independent package scaffolds and protocol-only dependency boundary created.
- Simulation-safe drivers/adapters, generated types, validation, and tests added.

## Remaining gate items

- None for Gate P0. Physical capability claims remain explicitly outside P0.

## Decisions and assumptions

- Python 3.11 standard library is sufficient for Phase 0; HTTP/FastAPI and
  Pydantic enter with API implementation rather than becoming unused dependencies.
- Protocol generation is deterministic and checked for drift.
- Simulator seed is `20260811`; simulation timestamps do not claim real timing.

## Known risks/blockers

- The supplied OpenAPI/AsyncAPI drafts receive deterministic structural checks;
  full standards-validator tooling remains a Phase 1 dependency decision.
- No physical capability, BLE behavior, acoustic accuracy, or real-room safety is verified.

## Last verification

```text
python scripts/tasks.py bootstrap -> pass, 2026-08-11
python scripts/tasks.py check -> pass; generated-client drift, boundaries, and 2 isolated product suites
python scripts/tasks.py contract -> pass; 7 contract tests
python scripts/tasks.py sim-smoke -> pass; seed 20260811, duplicate suppressed, final safe_hold
python scripts/tasks.py test -> pass; 19 tests plus isolated standalone repetitions
python scripts/tasks.py docs-check -> pass
```

## Hardware state

- Real R2 movement authorized for next run: no
- Last known droid state: unknown/stopped (never assume active)
- Capability profile: none/unverified
- Hardware evidence category: none

## Exact next task

Begin Phase 1 with the pinned/reviewed `spherov2.py` adapter and a stationary,
simulation/replay-first capability-probe path. Do not access hardware until the
operator explicitly authorizes the exact HIL test and completes preflight.
