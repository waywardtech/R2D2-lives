# Project status

Last updated: 2026-08-12
Current phase: Phase 1
Gate state: IN PROGRESS

## Current objective

Deploy and verify the stationary proof-of-life report and read-only iPhone
dashboard while keeping locomotion and every physical operation separately gated.

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
| R2-008 / bounded expressions | in_progress | proof-of-life simulation and failed HIL report | HIL failed before expression start; no primitive issued |
| R2-012 / Safari PWA | in_progress | `https://raspberrypi.local/R2D2/` | Read-only portrait dashboard live; auth/control gates pending |
| R2-014 / distinct health | pass | live dashboard status plus collector tests | Target-host Pi/R2 status and issue highlighting verified |
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
- Durable append-only encounter progress now records privacy-safe, fsynced stage
  markers around scan, connection, battery, every reaction, disconnect, failure,
  and completion. It rejects identity, addresses, exception text, unknown fields,
  and sequence tampering so future watchdog diagnosis does not depend on a final
  report. This improvement is simulation-verified and has not been run on hardware.
- Encounter progress now also rejects illegal state transitions, wrong
  stage-specific value types, and mismatched reaction order before append. An
  offline recovery command converts a verified or absent journal into immutable,
  deterministic, identity-free watchdog evidence with an exact stall class. A
  journal ending in completion remains a watchdog timeout, not a passing cycle.
- Commit `8c5bae3` passed hosted simulation CI run `31563552918` and was copied
  into rollback-safe Pi staging `/home/pi/r2d2-hil-8c5bae3`. Five changed-file
  hashes matched; the offline absent-journal recovery returned
  `watchdog_timeout`/`no_progress`. Bluetooth stayed soft-blocked and no droid
  discovery, connection, command, or actuation occurred.
- A separately armed external encounter watchdog now owns the 20-to-120-second
  child bound. It refuses stale output paths, automatically converts a timeout
  journal into immutable evidence, and states that BLE disconnect remains
  unverified and operator confirmation is required after process termination.
  Normal child exits pass through unchanged. This path is simulation-tested only.
- Commit `7c90a1f` passed hosted simulation CI run `31564021923` and was copied
  to rollback-safe Pi staging `/home/pi/r2d2-hil-7c90a1f`. Three hashes matched;
  its default invocation refused before child launch and created no output files.
  Bluetooth remained soft-blocked and no droid was accessed.
- The newly authorized encounter attempt stopped before scanner import because
  the staged launcher lacked its isolated dependency path. No scan, connection,
  droid command, or evidence file occurred; shutdown re-blocked Bluetooth. The
  launcher now owns that path explicitly and has a regression test.
- Commit `919713f` passed hosted CI run `31564493652` and its corrected staging
  completed discovery, connection, and the safe-battery gate. Reaction 1 started
  but raised `EOFError` before completion. The child reached
  `disconnect_started`; the external watchdog then terminated it at 40 seconds.
  Sanitized failure, progress, and watchdog evidence are preserved. Bluetooth
  was powered off and soft-blocked. No retry was made; operator observation is pending.
- Pinned-source inspection confirmed all expression primitives synchronously
  await firmware responses. The failure path now preserves a stable first-failed
  phase, attempts every restoration, and closes a transport after EOF without a
  second response-dependent motor-OFF wait. Injected EOF coverage passes; the
  prior HIL attempt's exact primitive remains unknown and no hardware retry occurred.
- Commit `c9f344e` passed hosted simulation CI run `31609883254` and was copied
  to rollback-safe Pi staging `/home/pi/r2d2-hil-c9f344e`. Five file hashes and
  the import-only default refusal passed with Bluetooth soft-blocked. No scan,
  connection, droid command, or HIL retry occurred.
- The operator closed attempt 3 observation: no sound, dome movement, or LED
  reaction was seen/heard; base, legs, heading, and location did not change; R2
  ended stationary, silent, with all LEDs off. This characterizes a safe observed
  final state but not acknowledged restoration or a passing HIL cycle.
- A seeded stationary proof-of-life path now reports Pi/R2 state and issues,
  flashes the verified logic-display bank, plays one verified R2 sound, and
  sweeps the dome within ±20 degrees before neutral restoration. It has no
  drive, heading, leg, or stock-animation path and passes simulation.
- An original X-wing-console-inspired portrait PWA now provides local R2 binary/
  Basic dialogue, animated decorative waveforms, and uncached ten-second status
  snapshots. The page is read-only and has no hardware command endpoint.
- Immutable Pi release `7ba7239` now serves `/R2D2/`; Apache syntax, private-LAN
  access over IPv4/IPv6, security headers, base redirect, status response, and
  the sandboxed ten-second refresher passed. Release `7adeab4` is retained for
  rollback.
- The one authorized proof-of-life HIL run connected and passed identity/battery
  gates, then failed with `EOFError` before `head_checked` or
  `expression_started`. No LED, audio, dome-set, drive, heading, leg, or animation
  primitive was issued. Disconnect completion was not journaled; the external
  watchdog terminated the process, Bluetooth was powered off, no connection or
  HIL process remained, and no retry occurred. The operator subsequently
  confirmed no sound, dome movement, or LED activity; no base, leg, heading, or
  location change; and a stationary, silent final state with all LEDs off. This
  closes direct physical observation but does not make the HIL cycle pass.
- A later authorized invocation failed closed before connection when two distinct
  live `D2-` advertisements appeared in two consecutive scans. A subsequent
  privacy-preserving 15-second packet sample observed only the expected one R2
  and one BB-8, with repeated fresh packets from each. This rules out a test
  fixture and makes a transient nearby R2-class advertiser the best current
  explanation; no droid was connected or commanded during diagnosis.
- Proof-of-life and encounter launchers now require the private configured R2
  identity before live discovery and select exactly one matching advertisement.
  Unrelated R2-class advertisements no longer create false ambiguity, while zero
  or duplicate exact matches still fail closed without persisting nearby names
  or addresses. This policy is simulation-tested only.
- Proof-of-life failures now retain stable session/subphase classification and
  sanitized exception type. A disconnect failure is reported separately as
  cleanup uncertainty and cannot overwrite the primary failure. Injected head
  EOF, unsafe-battery, primary-timeout, and disconnect-EOF scenarios all end
  offline/stopped in simulation; no firmware response is reinterpreted as
  success.
- A separately armed proof-of-life watchdog now owns the external child-process
  bound. It refuses reused evidence paths, preserves the durable stage journal,
  classifies the exact stalled boundary, terminates/kills a hung child, requires
  operator state confirmation, and never retries. This path is simulation-tested
  only and remains disabled by default.
- The R2 dashboard now renders English translations directly, without the
  redundant `Translation:` label or enclosing quotation marks; its offline
  cache revision was advanced so installed PWAs receive the presentation change.
- R2 English translation lines are now twice the base size, heavy-weight, set in
  a futuristic Latin font stack, and prefixed by a same-size right-facing
  triangle. Responsive wrapping and a new PWA cache revision ship the change.
- A deterministic static response-policy audit now verifies the pinned 0.12.1
  raw-motor DID/CID, requested-response flag, enqueue path, matching-ID wait, and
  ten-second timeout without importing the package or accessing BLE. It hashes
  reviewed sources, fails closed on drift, and keeps firmware behavior explicitly
  unverified pending the separately authorized bench trace.
- Pi release `045d251` ran that audit against the installed pinned source with
  Bluetooth inactive and soft-blocked. Immutable target evidence at
  `/var/lib/r2-runtime/evidence/response-policy-045d251.json` has SHA-256
  `23259f9268173b2a47601b00900a8aee302bb12c95b3e432c7b0c729f76b8418`;
  every client-side invariant passed, no BLE was accessed, and firmware response
  behavior remains unverified.
- The offline audit now covers a ten-entry stationary matrix: two battery
  queries, dome read/set, audio play/volume read/volume set/stop, and 16/32-bit
  LED setters. Every exact DID/CID path must pass through the same requested-
  response, matching-ID, ten-second client wait; this characterizes possible
  proof-of-life stall boundaries without attributing a cause to firmware.
- Pi release `9ae1835` ran the expanded audit against the installed pinned
  sources with Bluetooth inactive/blocked. All ten stationary command entries
  passed and immutable evidence SHA-256 is
  `105d76da6497bb3a526fc5c9c44e29ff5ad93d45235507b69a65603a129eda41`;
  it records `movement_performed: false` and `firmware_behavior: unverified`.
- A deterministic stop-response trace matrix now covers acknowledged success,
  firmware error, timeout, cleanup failure, and response-sequence mismatch.
  Every outcome fails closed as designed, output is seed-stable and identity-
  free, and the runner imports neither BLE nor vendor hardware code.
- A loopback-only FastAPI conversation service now backs dashboard chat through
  Apache. Strict Pydantic boundaries, a 280-character cap, SQLAlchemy 2 plus an
  Alembic migration, 40-turn-pair retention, opaque browser sessions, explicit-
  name continuity, and a visible browser fallback are implemented. The service
  exposes no BLE, driver, shell, arbitrary-URL, or physical-command surface.
- R2's local dialogue profile is grounded in official StarWars.com sources: the
  reliable, versatile, brave and loyal astromech communicates through emotional
  electronic whistles/beeps, with readable Basic shown only as a display
  translation. His dry, mouthy, resourceful and occasionally stubborn edge is
  retained without inventing canon memories.
- A provider-neutral OpenAI-compatible reasoning adapter is simulation-tested.
  It has no tools or physical authority, accepts only a strict two-field text
  response, bounds history/status context, rejects redirects and insecure
  endpoints, and falls back locally on response or transport faults. The Pi has
  no configured model credential, so its live service remains in local mode.
- The deterministic local dialogue now supports bounded issue summaries,
  identity/capability/mood questions, thanks and farewells, preferred-name and
  last-topic recall, and explicit repair for ambiguous yes/no replies. Keyword
  matching uses word boundaries so ordinary words cannot accidentally resemble
  movement or greeting commands; physical control remains absent.
- The PWA now shows whether a reply came from the model, local policy, safe
  model fallback, or browser fallback. One-tap identity, mood, issue, and recall
  prompts support operator dialogue testing, and the browser rejects any API
  response not explicitly marked `physical_action: false`. Cache revision v7
  delivers the UI change to installed clients.
- Pi release `9e7cfda` deployed the chat service under the sandboxed `r2-chat`
  account. Apache proxy syntax, `/health`, HTTPS chat, movement refusal, Alembic
  revision `0001_chat_continuity`, and two-turn preferred-name recall all passed;
  every response reported `physical_action: false`. The dashboard remained HTTP
  200 and Bluetooth remained inactive and soft-blocked.
- Pi release `e0c54fe` deployed the optional safe model adapter without enabling
  a provider or installing a credential. Loopback health and public HTTPS chat
  passed in `local` mode with `physical_action: false`; the dashboard returned
  HTTP 200, `r2-chat` remained active, and Bluetooth remained inactive and
  soft-blocked. No droid discovery, connection, or command occurred.
- Pi release `ccd552a` deployed the response-source chip and one-tap dialogue
  tests. The served HTML, JavaScript, and cache v7 were verified over HTTPS; a
  live issue query returned `mode: local` and `physical_action: false`.
  Bluetooth remained inactive and soft-blocked, with no droid access.

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
python scripts/tasks.py quality -> pass; Ruff format/lint and strict mypy, 53 source files
python scripts/tasks.py check -> pass; quality, generated-client drift, boundaries, and 2 isolated product suites
python scripts/tasks.py contract -> pass; 8 contract tests
python scripts/tasks.py sim-smoke -> pass; seed 20260811, duplicate suppressed, final safe_hold
python scripts/tasks.py docs-check -> pass
python scripts/verify_repository_hygiene.py -> pass; tracked secrets/device identities and dependency notices
python scripts/tasks.py p1-sim -> pass; five simulated cycles, virtual 1800 s soak, no movement, safe_hold
python scripts/tasks.py test -> pass; 120 primary suite tests plus isolated standalone repetitions
python scripts/tasks.py encounter-sim -> pass; BB-8 classified, 3 bounded reactions, no movement, offline
python scripts/tasks.py proof-of-life-sim -> pass; seeded sound, LED flashes, bounded dome sweep, offline
python scripts/tasks.py stop-trace-sim -> pass; 5 deterministic non-BLE classifier outcomes
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
GitHub Actions simulation-ci run 31563552918 -> pass; 95 tests and watchdog recovery evidence
GitHub Actions simulation-ci run 31564021923 -> pass; 100 tests and external watchdog coverage
Pi encounter staging -> pass; 6 hashes/versions verified, default HIL refusal before BLE
Pi progress staging 8c5bae3 -> pass; 5 source hashes matched, offline recovery passed, Bluetooth blocked
Pi watchdog staging 7c90a1f -> pass; 3 hashes matched, default refused, Bluetooth blocked
stationary droid encounter attempt 1 -> expression observed; timed out, normal final state, not a passing cycle
Pi dashboard deployment -> pass; active immutable release 7ba7239, HTTPS page/status and timer healthy
Pi static response-policy audit -> pass; client wait policy verified, firmware behavior unverified, no BLE
Pi conversation service -> pass; HTTPS local chat, migration, continuity, movement refusal, no physical action
Pi safe model-adapter rollout -> pass; release e0c54fe, local mode, no credential, Bluetooth inactive/blocked
stationary proof-of-life attempt 1 -> failed before expression start; watchdog cleanup, no retry
proof-of-life attempt 1 operator observation -> no expression or locomotion observed; stationary, silent, LEDs off
```

## Hardware state

- Real R2 movement authorized for next run: no
- One stationary proof-of-life expression authorized for next run: no; authorization consumed
- Last known droid state: operator-confirmed stationary and silent with all LEDs off; controller powered off with no BLE connection or HIL process
- Capability profile: partial; firmware/identity/battery/advertised telemetry observed
- Hardware evidence category: target-host import, HIL discovery, and failed stationary probe

## Exact next task

The response-policy diagnosis has reached its hardware boundary: static source
audit and the complete deterministic trace-classifier matrix pass. The next
question--whether firmware 7.0.101 acknowledges the one OFF/0 raw-motor packet--
requires the separately authorized physical stop-response bench, exact preflight,
and a demonstrated immediate shutdown method. Do not run it while charging or
reuse earlier proof-of-life authorization. Locomotion remains unauthorized.
