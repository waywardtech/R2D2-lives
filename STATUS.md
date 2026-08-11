# Project status

Last updated: 2026-08-11  
Current phase: Phase 1
Gate state: IN PROGRESS

## Current objective

Complete the Phase 1 stationary capability-probe dependency and simulation
evidence while keeping all physical operations separately gated.

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
| R2-001 / single BLE owner | in_progress | `r2_runtime.ble_owner.BleOwner` | Simulation verified; real process/HIL pending |
| R2-002, R2-003 / capability probe | in_progress | `python scripts/tasks.py p1-sim` | Actual R201 firmware remains unverified |
| R2-004 / reconnect no-resume | pass | `test_link_loss_and_reconnect_do_not_resume` | Simulation evidence |
| Gate P1 / five cycles | incomplete | five simulation cycles | Five real HIL cycles required |
| Gate P1 / 30-minute session | incomplete | 1,800-second virtual soak | Real stationary HIL session required |
| Gate P1 / bounded movement | incomplete | none | Explicit motion authorization and preflight required |

Evidence category: automated, contract, simulation. No HIL evidence.

## Completed this phase

- Specification pack checksum verified and source-of-truth copied under `specs/`.
- Independent package scaffolds and protocol-only dependency boundary created.
- Simulation-safe drivers/adapters, generated types, validation, and tests added.
- Phase 0 passed and was committed as `5184358`.
- Phase 1 simulation/replay stationary probe, BLE-owner state machine, immutable
  report evidence, and disabled HIL entry point implemented.
- Upstream `spherov2` 0.12.1 source archive/license verified by SHA-256 and a
  lazy, exact-identity R2 adapter implemented without importing or using BLE in tests.
- Target CPython 3.11 Linux/aarch64 hardware wheel set resolved into a six-artifact
  hash lock and manifest; downloaded wheels verified without installation.
- All six locked packages installed offline and imported successfully with
  Python 3.11.2 on the Debian 13/aarch64 target host; BLE was not accessed.
- Read-only Pi readiness audit passed for BlueZ, D-Bus, NTP, storage, and CPU
  thermal state; the Bluetooth controller remains powered off and undiscoverable.
- First authorized stationary discovery attempt characterized the Pi's software
  rfkill state but found no R2 advertisement; no connection or command occurred.

## Remaining gate items

- After explicit stationary-HIL authorization and preflight: run five real
  connect/probe/disconnect cycles and a 30-minute stationary session.
- After separate explicit motion authorization: run the <=0.25 m calibration
  and emergency-stop subtest. Failure must end the sequence without retry.

## Decisions and assumptions

- Python 3.11 standard library is sufficient for Phase 0; HTTP/FastAPI and
  Pydantic enter with API implementation rather than becoming unused dependencies.
- Protocol generation is deterministic and checked for drift.
- Simulator seed is `20260811`; simulation timestamps do not claim real timing.
- The external droid identity is configuration-only and capability evidence does
  not store it. Public model/system values form a one-way local device reference.

## Known risks/blockers

- The supplied OpenAPI/AsyncAPI drafts receive deterministic structural checks;
  full standards-validator tooling remains a Phase 1 dependency decision.
- No physical capability, BLE behavior, acoustic accuracy, or real-room safety is verified.
- Target-host dependency imports are verified, but the Pi defaults to Python
  3.13.5 and deployment must explicitly use 3.11. All actual firmware/BLE behavior remains unverified.
- R2 did not advertise during bounded discovery while charging; operator action
  is required to wake advertising without moving or unplugging the droid.

## Last verification

```text
python scripts/tasks.py bootstrap -> pass, 2026-08-11
python scripts/tasks.py check -> pass; generated-client drift, boundaries, and 2 isolated product suites
python scripts/tasks.py contract -> pass; 7 contract tests
python scripts/tasks.py sim-smoke -> pass; seed 20260811, duplicate suppressed, final safe_hold
python scripts/tasks.py test -> pass; 19 tests plus isolated standalone repetitions
python scripts/tasks.py docs-check -> pass
python scripts/tasks.py p1-sim -> pass; five simulated cycles, virtual 1800 s soak, no movement, safe_hold
python scripts/tasks.py test -> pass after Phase 1 lock slice; 43 tests plus isolated standalone repetitions
python scripts/verify_hardware_lock.py --wheelhouse <temp> -> pass; 6 Linux/aarch64 wheels
SSH target-host check -> pass; Python 3.11.2, Debian 13/aarch64, 6 isolated imports, no BLE
SSH Pi readiness audit -> pass; BlueZ 5.82 active, NTP synchronized, controller powered off
stationary HIL discovery attempt 1 -> blocked; no R2 advertisement, no connection/command
```

## Hardware state

- Real R2 movement authorized for next run: no
- Last known droid state: unknown/stopped (never assume active)
- Capability profile: none/unverified
- Hardware evidence category: target-host import plus HIL discovery; no R2 connection

## Exact next task

Run only the stationary HIL preflight/probe after explicit operator authorization.
Movement remains a later, separately authorized final subtest.
