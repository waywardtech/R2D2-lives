# 09 - Roadmap and acceptance gates

## Guiding allocation

R2 Agent Runtime receives development focus until the R2 MVP gate passes. Work done before that gate on BSM is limited to SAP schemas, generic simulators, integration stubs, and requirements needed to prevent architectural blockers. Acoustic solver development starts afterward.

No phase advances because code exists; it advances when evidence satisfies the gate.

## Phase 0 - Contract and workspace foundation

### Deliver

- repository/workspace scaffold and `AGENTS.md`;
- SAP schema package, examples, generated clients, and conformance harness;
- R2 and BSM package boundaries with CI cross-import checks;
- SimDroidDriver, SimSpatialProvider, and generic SimMobileAgent skeletons;
- event envelope, units/time/frame/covariance library;
- `STATUS.md`, ADR and traceability workflow;
- no physical actuation.

### Gate P0

- Both products build/test when the other's source directory is absent.
- Protocol schemas and valid/invalid fixtures pass.
- A simulated command/event/session round trip preserves IDs, time, frames, units, and uncertainty.
- R2 selects NullSpatialProvider/SimSpatialProvider by configuration.
- BSM skeleton selects SimMobileAgent without importing R2.

## Phase 1 - R2 hardware capability probe

### Deliver

- pinned/reviewed `spherov2.py` adapter;
- configurable droid discovery and persistent BLE owner;
- stationary capability probe report;
- low-risk LED/head/audio/telemetry/battery tests;
- separately armed low-speed movement/calibration test;
- raw session recorder/replay fixture;
- safe shutdown/reconnect.

### Gate P1

- Five connect/probe/disconnect cycles succeed or failures are characterized and fixed.
- One persistent 30-minute stationary session has no uncaught error.
- Capability report identifies verified, failed, unsupported, and untested features for the actual firmware.
- Disconnect/reconnect never resumes motion.
- A bounded <=0.25 m supervised calibration movement stops through both command completion and emergency path.
- Operator-preflight and HIL evidence are saved without committing MAC address or secrets.

## Phase 2 - R2 deterministic control core

### Deliver

- safety executive, priority arbitration, motion lease/watchdog;
- typed command lifecycle and SAP Agent API/events;
- bounded manual PWA with deadman and emergency stop;
- telemetry/health, collision and stuck inference;
- deterministic expression compiler and preview;
- continuity event store, migrations, backup/restore;
- SimDroid parity and fault matrix;
- Pi package/`systemd`/Apache integration.

### Gate P2

- Unit/component/contract/simulation suites pass.
- Local stop dispatch P95 <=300 ms and LAN stop dispatch P95 <=500 ms under defined Pi load, excluding mechanical stopping distance.
- Lease/watchdog stops on controller crash and heartbeat loss in every injected run.
- Duplicate/stale/out-of-order commands never cause duplicate motion.
- Eight-hour supervised stationary/simulated service soak meets memory/temperature/backlog limits.
- Reboot returns stopped and healthy; backup/restore demonstrated.
- SimSpatialProvider can create a session and send accepted/rejected advisories through SAP.

## Phase 3 - R2 interaction, Discovery, and Continuity

### Deliver

- wake/VAD/STT adapters and offline critical intent path;
- `smolagents` ToolCallingAgent adapter with typed high-level tools;
- R2 expression lexicon;
- speaker-attention zone input and look behavior;
- supervised Discovery behavior tree;
- patrol route model (execution may remain limited);
- Talk-to-Tag, referent confirmation, entity/alias search;
- PWA transcripts/tags/timeline/provider state;
- read-only sanitized information integration boundary (email adapter can remain mocked until credentials are configured).

### R2 MVP gate

- `stop`, `status`, `quiet`, and cancel work without LLM/internet.
- Removing smolagents, STT, email, BSM, or internet independently does not break deterministic/manual core.
- Wake false-accept/false-reject and command latency are measured in the actual office; selected thresholds are documented rather than assumed.
- Seeded Discovery scenarios enforce segment/geofence/safety limits and stop on repeated encounters/uncertainty.
- Supervised real Discovery completes a bounded session without leaving its configured area.
- Talk-to-Tag deterministic corpus resolves or asks clarification correctly in >=95% of labeled cases; no silent wrong grounding in safety-relevant cases.
- Continuity survives reboot and can show provenance for "edge of carpet"-style tags.
- Generic Agent SAP conformance passes.
- R2 can complete a simulated mapping-mission handshake/hold/probe flow with SimSpatialProvider.
- Install, upgrade, rollback, backup, restore, and operator docs pass on the Pi.

## Phase 4 - BSM standalone simulation foundation

Begins only after the R2 MVP gate, aside from Phase 0 scaffolding.

### Deliver

- BSM API, mission engine, artifact/metadata stores;
- generic SAP MobileAgent client and SimMobileAgent profiles;
- deterministic acoustic simulator and canonical fixtures;
- probe catalog, capture metadata, clock/calibration models;
- replaceable detector/localizer/surface/world-model interfaces;
- diagnostic plots and immutable map revisions.

### Gate P4

- BSM builds/tests with R2 absent.
- Floor-rover and 6DoF drone profiles execute capability-appropriate simulated missions without solver code changes.
- Ideal known-probe delay estimate error <=1 sample.
- In synchronized synthetic SNR >=20 dB reference cases, source-localization median error <=0.05 m and P95 <=0.15 m, with failures reported separately.
- Simple shoebox synthetic first-order wall-plane distance median error <=0.10 m under the declared fixture.
- Repeated run with identical seed/evidence/config produces identical manifest and numerically bounded deterministic results.
- Unobservable/poor-clock cases abstain or degrade; they do not publish a `valid` map.

These thresholds are engineering targets for the defined synthetic fixtures, not predictions of phone-array performance.

## Phase 5 - BSM physical bench and microphone nodes

### Deliver

- native capture node for the first PC/interface and adapters for available phones/Pi;
- node enrollment, sample/clock/channel/source calibration;
- stationary known-source experiments;
- environmental/speed-of-sound metadata;
- measured phone/browser processing/latency limitations;
- controlled-room reference measurements.

### Gate P5

- Shared-clock array capture has no unexplained channel drop/skew in a 30-minute bench run.
- Calibration artifacts and uncertainty reproduce from a second run.
- Known stationary source real-room median localization error <=0.25 m and P95 <=0.50 m inside the declared calibrated volume.
- Gross wall-plane distance error <=0.30 m for validated visible reference walls in the controlled room, or the phase remains research-only.
- Heterogeneous phone results are separately reported and never substituted for synchronized-array gates.
- Probe level/duty and microphone privacy/operator controls pass.

## Phase 6 - First mandatory R2 + BSM integration

### Deliver

- BSM connects only through R2's existing SAP Agent API;
- stationary probe mission, then bounded pose/rotate/hold/probe mission;
- time/frame/odometry/world transform estimation;
- BSM map/advisory displayed in both systems;
- semantic tag to BSM feature link;
- full record/replay and provider-loss recovery.

### Gate P6

- INT-S01 through INT-S06 pass.
- No R2 or BSM private type/import/database appears across the boundary.
- BSM can swap to SimMobileAgent and R2 can swap to SimSpatialProvider without code change.
- Provider/network loss during every mission state leaves R2 safe-held and no automatic resume.
- Actual probe emissions, captures, poses, clocks, map revision, and advisory correlate by IDs/hashes.
- Advisories outside freshness/frame/uncertainty policy are rejected with stable reason codes.
- First integrated map has independent real-room error measurements and is labeled with its supported operating envelope.

## Phase 7 - Operational spatial assistance

### Deliver

- repeated mapping and map-change comparison;
- validated world-to-odom correction and conservative hazard/corridor advisories;
- patrol/discovery use of fresh advisory information;
- route review/approval UI;
- additional generic agent adapter proof.

### Gate P7

- Real-room error and confidence remain within declared limits over repeated days/conditions.
- R2 never treats unknown space as free.
- Approved-route trials demonstrate safe pause/hold on degraded localization, changed geometry, node loss, and stale revisions.
- A second non-R2 agent simulator or physical agent passes the relevant BSM profile without mapping-core changes.

Collision-prevention claims require a separate quantified safety validation; completing P7 alone does not grant one.

## Phase 8 - Research stretch goals

- microphone self-localization and more complete blank-slate initialization;
- dynamic/change classification;
- multi-agent cooperative mapping;
- camera/other-sensor fusion through separate evidence adapters;
- object identification;
- operator-approved object tracking;
- intercept/orbit only after a dedicated safety/privacy design and validation.

Each stretch feature begins observation/simulation-only and receives its own ADR, threat/hazard analysis, requirements, and gates.

## Release readiness checklist

- All requirements for the milestone traced to passing evidence
- Standalone builds and SAP conformance pass
- Safety invariants/fault matrix pass
- Configuration and migration compatibility documented
- Logs/metrics/alerts and data retention verified
- SBOM/license/security scan reviewed
- Simulation/HIL/real-room claims labeled correctly
- Operator install, preflight, stop, recovery, backup, and rollback demonstrated
- Known limitations and next risk published
- R2 physically stopped and requires fresh operator arming after release

