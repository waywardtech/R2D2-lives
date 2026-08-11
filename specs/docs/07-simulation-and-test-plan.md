# 07 - Simulation and test plan

## 1. Test philosophy

Simulation is the default development environment and a first-class product capability. Real hardware validates adapters and physics; it does not replace deterministic unit, contract, and scenario tests.

Every requirement maps to at least one verification method in `traceability/requirements.csv`:

- inspection;
- automated test;
- simulation with ground truth;
- hardware-in-loop (HIL);
- calibrated real-room experiment;
- operator demonstration.

## 2. Required simulators

### 2.1 SimDroidDriver

Models:

- connection/handshake and configurable command latency;
- R2 command queue and safe interval;
- pose, velocity, locator drift, attitude, gyro, acceleration;
- battery discharge/state transitions;
- collisions, stuck conditions, tilt/fall, disconnects;
- head/leg/LED/audio/animation state;
- command rejection/timeout/duplicate behavior.

It records all requested primitives so expression and safety tests can assert exact bounded output.

### 2.2 SimMobileAgent

A generic SAP agent independent of R2 with configurable footprint, 2D/3D dynamics, clocks, probe sources, and capabilities. At least two profiles are required:

- floor rover with R2-like constraints;
- six-degree-of-freedom drone profile.

BSM must run against both without mapping-algorithm changes.

### 2.3 SimSpatialProvider

Provides deterministic world/odom transforms, hazards, routes, delays, stale revisions, impossible jumps, dropouts, and confidence changes. It proves R2 is provider-neutral before BSM exists.

### 2.4 Acoustic room simulator

Generates known probe recordings and metadata from:

- room/surface geometry and absorption;
- microphone/source positions and responses;
- direct path/reflections and optional moving objects;
- sample clocks, offset, drift, jitter, buffering, dropouts;
- noise, clipping, AGC/nonlinear distortion;
- agent motion/pose error;
- environmental speed of sound.

Ground truth is stored outside estimator inputs. The simulator must support simple analytic fixtures whose answers are independently calculable, plus an optional third-party acoustics backend.

## 3. Record and replay

A session recorder captures:

- SAP commands/events and cursors;
- raw driver events (redacted as needed);
- configuration/build/protocol versions;
- clock/calibration records;
- artifact hashes and optional local artifacts;
- random seeds and simulator truth when applicable.

Replay modes:

- original timing;
- accelerated deterministic timing;
- step-by-step;
- fault injection at chosen event IDs;
- algorithm A/B comparison against identical evidence.

Replays never send commands to real hardware.

## 4. Test layers

| Layer | Scope | External dependencies |
|---|---|---|
| Unit | pure policy, parsing, transforms, signals, state machines | none |
| Property | units, frames, idempotency, invariants, numerical ranges | none |
| Component | DB, driver fake, API, event stream, audio fixture | local only |
| Contract | Agent/Provider schemas and behavior | simulators/loopback |
| Integration | multi-service vertical slice | local processes/containers |
| Simulation | agent plus room/mics/BSM with ground truth | deterministic local |
| HIL | Pi BLE/audio with R2 stationary/bounded | explicit supervised hardware |
| Real room | calibrated mapping and independent measurements | controlled lab/office |
| Soak/performance | long-running reliability and resource budgets | sim then supervised hardware |

## 5. Core safety test matrix

Every motion command type is tested for:

- valid acceptance and terminal completion;
- missing/expired lease;
- stale deadline;
- duplicate idempotency key;
- cancellation before and during execution;
- controller crash/heartbeat loss;
- BLE disconnect/reconnect;
- collision, stuck, tilt, low battery, geofence, and speed cap;
- stale/low-confidence spatial advisory;
- out-of-order/duplicate events;
- stop preemption under CPU/audio/model load;
- service restart without movement resume.

An assertion must verify the final driver primitive is stop/safe state, not merely that an exception occurred.

## 6. R2 functional scenarios

### R2-S01: Capability probe

Stationary by default; verifies identity, firmware/system info, battery, LEDs at low brightness, head within safe range, quiet audio preview, telemetry streams, and collision configuration. Movement is a separately armed final subtest.

### R2-S02: Manual bounded movement

Operator arms a clear area, commands <=0.25 m at low speed, observes measured travel, stops, and records calibration.

### R2-S03: Stop under failure

Inject web disconnect, worker crash, stale command, and BLE fault. Confirm lease expiry and no auto-resume.

### R2-S04: Expression compiler

For each lexicon meaning and system state, assert media primitives are verified, bounded, quiet-mode compliant, and repeat-suppressed.

### R2-S05: Discovery

Seeded simulator run proves short segment bounds, pauses, collision recovery, interruption, battery exit, and semantic encounter creation. Real run is supervised only after sim pass.

### R2-S06: Talk-to-Tag

Create multiple recent observations and deictic utterances. Assert correct resolution, disambiguation, alias persistence, restart recovery, and later map-feature attachment.

### R2-S07: Voice degradation

Disable wake, STT, model, internet, and email independently. Stop/status/manual core remains available by required local interfaces.

### R2-S08: Provider substitution

Run identical R2 scenario against NullSpatialProvider and SimSpatialProvider. No product code change; behavior changes only by capability/configuration.

## 7. BSM functional scenarios

### BSM-S01: Ideal timing fixture

Known single source and microphones; direct-path delay detection error <=1 sample in noise-free synthetic input.

### BSM-S02: Clock faults

Inject offset, drift, jitter, and a node resample. Solver either corrects within declared uncertainty or reports degraded/insufficient observability.

### BSM-S03: Known array source localization

Sweep positions in a calibrated simulated room; report median, P95, bias, covariance coverage, and failures.

### BSM-S04: Surface estimation

Shoebox and non-rectangular simulated rooms with held-out emissions; compare plane position/orientation and free/unknown classification.

### BSM-S05: Blueprint prior

Run with no prior, correct prior, and deliberately wrong prior. Wrong prior must not overwrite contradictory evidence silently.

### BSM-S06: Generic agents

Run the same mission planner with floor rover and drone capability profiles; unsupported movements yield alternative plans/rejections.

### BSM-S07: Missing node/evidence

Drop one/multiple channels, clip probes, and move a mic. Observability and map confidence change visibly; no false success.

### BSM-S08: Immutable revisions

Reprocess identical evidence with a new solver/config. Produce a child map revision with preserved parents/artifact hashes.

## 8. First integration scenarios

### INT-S01: Capability/session handshake

BSM negotiates with R2 via SAP, selects supported probe/hold/pose features, and records version/clock/frame state.

### INT-S02: Stationary probe

R2 remains stationary, BSM arms nodes, requests an emission, receives actual emission evidence, ingests recordings, and publishes a diagnostic result.

### INT-S03: Bounded mapping step

BSM requests a safe pose/rotation and hold; R2 independently validates/executes; a probe is captured; command and evidence correlate end-to-end.

### INT-S04: Network/provider loss

Disconnect BSM during movement/hold/capture. R2 safe-holds according to lease/policy and never resumes when connection returns.

### INT-S05: Advisory consumption

BSM publishes a time-bounded transform/hazard/route advisory. R2 validates revision/frame/uncertainty and accepts, modifies, or rejects with reason.

### INT-S06: Semantic-spatial link

An R2 encounter/tag is linked to a BSM feature without either system writing the other's DB; later map revision preserves/reprojects the link.

## 9. Numerical verification

Every spatial benchmark reports:

- test/scenario version and seed;
- dataset/evidence hashes;
- calibration and clock assumptions;
- error distribution (median, mean, P90/P95, max, bias);
- success/failure/abstention count;
- uncertainty calibration/coverage;
- compute time, CPU/GPU, and memory;
- algorithm/config/build version.

A solver that abstains appropriately can outperform one with a lower mean error but unsafe false confidence. Acceptance includes failure detection.

## 10. Performance and resource tests

### Raspberry Pi

- stop dispatch latency under simultaneous audio/STT, web, persistence, and telemetry load;
- CPU temperature and throttling;
- memory high-water and leak over 8 hours;
- event backlog/disk growth;
- BLE reconnect and packet error rate;
- audio underrun/overrun and wake false-trigger metrics.

Safety capacity is reserved; optional workers are throttled/killed before core control is starved.

### BSM host

- real-time ingest capacity by channels/sample rate;
- processing time per emission/minute of audio;
- memory/artifact growth;
- job cancellation/restart and partial evidence;
- map revision/query latency;
- CPU-only baseline and optional acceleration comparison.

## 11. HIL rules

- Mark tests `hardware`, `motion`, `audio_probe`, or `destructive_to_state` as applicable.
- Disabled by default and never selected by a general `test` command.
- Require exact device identity, operator confirmation, environment preflight, bounded parameters, and a stop control.
- Stationary HIL runs before motion HIL.
- Failure ends the sequence; no automated retries of a physical motion.
- Record measured results and preserve previous capability/calibration profile.

## 12. CI gates

Every pull request:

- formatting/lint/type checks;
- unit/property/component tests;
- JSON Schema/OpenAPI validation;
- agent/provider conformance tests;
- standalone dependency-boundary checks;
- deterministic simulation smoke suite;
- migration upgrade/downgrade or restore test as defined;
- secret/dependency/license scan;
- PWA unit/accessibility tests.

Nightly/release:

- full seeded simulation matrix;
- record/replay corpus;
- numerical regression and confidence coverage;
- service integration/soak;
- browser end-to-end tests;
- build/package for Pi and BSM platforms;
- HIL only on a separately authorized local runner.

## 13. Test artifacts

Keep small canonical fixtures in Git where licensing/privacy allow. Larger recordings/maps use a versioned artifact manifest and content hashes. Never commit personal email, uncontrolled room recordings, tokens, or device MAC addresses.

