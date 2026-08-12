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
| R2-002, R2-003 / capability probe | in_progress | `evidence/hil/cycle-1-stop-timeout.json` | Firmware observed; stop and optional actions incomplete |
| R2-004 / reconnect no-resume | pass | `test_link_loss_and_reconnect_do_not_resume` | Simulation evidence |
| Gate P1 / five cycles | incomplete | five simulation cycles | Five real HIL cycles required |
| Gate P1 / 30-minute session | incomplete | 1,800-second virtual soak | Real stationary HIL session required |
| Gate P1 / bounded movement | incomplete | none | Explicit motion authorization and preflight required |

Evidence category: automated, contract, simulation, HIL failure. No passing HIL cycle.

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
- Second discovery classified one R2-D2 and one BB-8 without connecting either;
  hardware modules now import without SAP or peer-product source.
- Exact-identity HIL observed firmware 7.0.101 and battery 3.77 V/ok; both
  zero-speed stop forms timed out, but fixed cleanup closed BLE without retry.
- The operator confirmed R2 returned to its normal silent, LEDs-off state after
  the optional-pass watchdog; no further charging-state actions were attempted.
- Deterministic, privacy-safe BLE-owner lifecycle recording and strict replay
  validation now cover sequence, clocks, state transitions, redaction, tampering,
  recorder failure isolation, and a reviewed stationary simulation fixture.
- A non-executing stop-response bench procedure defines the exact one-command
  limit, privacy-safe capture, physical shutdown prerequisite, abort conditions,
  cleanup, and evidence classifications. No new hardware action was taken.
- A simulation-only stop-response metadata recorder now admits exactly one raw
  motor OFF command observation, hashes/discards encoded bytes, correlates at
  most one response, rejects retries/tampering, and fails timeout closed as
  `stop_unconfirmed`. It is not connected to the hardware transport.
- An opt-in, fake-vendor-tested observer seam now uses the pinned library's exact
  encode/execute path without altering flags, timeout, or error semantics. The
  default backend remains unchanged; only the separately gated bench runner
  enables the seam.
- A separately marked stop-response bench runner is implemented and verified to
  refuse its default invocation. It requires an external exact arm token, all
  physical/clock gates, one owner-disconnect OFF/0 attempt, zero residual BLE
  connections, and interactive post-test confirmation; it has not been run.
- Bench-result simulation preserves an operator-confirmed response timeout as
  `stop_unconfirmed`, while unsafe battery, missing confirmation, and unrelated
  execution errors remain `invalid_test` rather than being conflated.
- Bench session orchestration is now owned by R2 Runtime and simulation-tested
  across success, response timeout, unsafe battery, and battery-query failure;
  every connected case performs one stop attempt and one BLE disconnect.
- A least-privilege GitHub Actions workflow now runs Python 3.11 checks, contract
  and standalone suites, deterministic simulations, and documentation evidence.
  A static CI guard rejects HIL entry points, hardware identity/arm variables,
  Bluetooth/SSH/sudo commands, and self-hosted runners.
- The first hosted run reached post-job cleanup but failed because pip caching was
  configured for a dependency-free workflow. The cache was removed and official
  checkout/setup actions were advanced to their Node 24 releases. The corrected
  hosted run passed all simulation-only jobs.
- Hosted third-party actions are pinned to immutable commits resolved from the
  official checkout/setup-python v6 tags; the CI guard rejects floating major tags.
- Offline repository hygiene now scans tracked files for credential/private-key
  formats, BLE addresses, private advertised identities, and forbidden credential
  filenames, and verifies every locked hardware dependency has license notices.
- An exact, hash-locked Ruff 0.15.22 and mypy 2.3.0 toolchain now runs in local
  `check`/`test` and hosted CI. Formatting, lint, and strict typing pass across
  36 source files; malformed JSON evidence, manifests, and schema references
  now fail at their typed boundaries.
- Nearby Sphero advertisements can now be reduced to privacy-safe droid classes
  and passed through the owned chat seam for semantic selection. A deterministic
  compiler owns R2-only sound selection, prevents immediate repetition, bounds
  dome gestures to ±20 degrees, restores head/audio/LED state, and forbids drive,
  heading, legs, and unverified stock animations. Simulation passes; live head
  and audio evidence awaits completion of the explicit physical preflight.
- Commit `ed76384` passed hosted simulation CI run 31552293911. Its exact
  six-wheel hardware profile was re-verified and installed offline into isolated
  Pi staging `/home/pi/r2d2-hil-ed76384`; all locked versions match and the
  staged encounter command refuses by default before Bluetooth access.
- The first confirmed live encounter attempt passed physical/machine preflight
  but its 40-second watchdog expired without a report. Python terminated; one
  residual BLE link was dropped by powering off/soft-blocking the controller,
  leaving zero connections. No retry was made. Whether head/audio primitives
  visibly completed was initially indeterminate. The operator subsequently
  confirmed an expression was seen/heard and that R2 ended stationary, silent,
  and in its normal LED state. Individual primitive completion is not known, and
  the timed-out session does not count as a passing HIL cycle.

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
- Some physical identity, battery, and BLE behavior is observed; acoustic accuracy
  and real-room safety remain unverified.
- Target-host dependency imports are verified, but the Pi defaults to Python
  3.13.5 and deployment must explicitly use 3.11. All actual firmware/BLE behavior remains unverified.
- R201 firmware 7.0.101 does not acknowledge drive stop commands while charging.
  The failed cycle disconnects safely but cannot count as Gate P1 success.
- Sphero's public packet protocol permits commands to omit a requested response,
  while pinned `spherov2.py` 0.12.1 waits synchronously for every command. Source
  inspection cannot distinguish a charging-state behavior from an unsupported
  response assumption. Treating packet transmission as stop confirmation is
  prohibited until a separately authorized bench trace resolves the ambiguity.

## Last verification

```text
python scripts/tasks.py bootstrap -> pass, 2026-08-11
python scripts/tasks.py quality -> pass; Ruff format/lint and strict mypy, 41 source files
python scripts/tasks.py check -> pass; quality, generated-client drift, boundaries, and 2 isolated product suites
python scripts/tasks.py contract -> pass; 7 contract tests
python scripts/tasks.py sim-smoke -> pass; seed 20260811, duplicate suppressed, final safe_hold
python scripts/tasks.py docs-check -> pass
python scripts/verify_repository_hygiene.py -> pass; tracked secrets/device identities and dependency notices
python scripts/tasks.py p1-sim -> pass; five simulated cycles, virtual 1800 s soak, no movement, safe_hold
python scripts/tasks.py test -> pass; 82 primary suite tests plus isolated standalone repetitions
python scripts/tasks.py encounter-sim -> pass; BB-8 classified, 3 bounded reactions, no movement, offline
python scripts/verify_hardware_lock.py --wheelhouse <temp> -> pass; 6 Linux/aarch64 wheels
SSH target-host check -> pass; Python 3.11.2, Debian 13/aarch64, 6 isolated imports, no BLE
SSH Pi readiness audit -> pass; BlueZ 5.82 active, NTP synchronized, controller powered off
stationary HIL discovery attempt 1 -> blocked; no R2 advertisement, no connection/command
stationary HIL discovery attempt 2 -> pass; one R2 and one BB-8 type-filtered, no connection/command
stationary HIL probe attempt 1 -> failed; stop acknowledgement timeout, BLE disconnected, no movement
GitHub Actions simulation-ci run 31550425423 -> pass; Python 3.11 hosted runner, no HIL/hardware path
GitHub Actions simulation-ci run 31551031074 -> pass; repository hygiene and immutable action pins
GitHub Actions simulation-ci run 31551472563 -> pass; hash-locked quality tools, 67 tests, simulations, docs
GitHub Actions simulation-ci run 31552293911 -> pass; 82 tests and stationary droid-encounter simulation
Pi encounter staging -> pass; 6 hashes/versions verified, default HIL refusal before BLE
stationary droid encounter attempt 1 -> expression observed; timed out, normal final state, not a passing cycle
```

## Hardware state

- Real R2 movement authorized for next run: no
- Last known droid state: disconnected, silent, and normal LEDs/off per operator confirmation
- Capability profile: partial; firmware/identity/battery/advertised telemetry observed
- Hardware evidence category: target-host import, HIL discovery, and failed stationary probe

## Exact next task

Do not retry the live session. Add stage-level durable observability in
simulation before considering another separately authorized HIL run. The
stop-response bench remains blocked while charging.
