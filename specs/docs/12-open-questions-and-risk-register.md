# 12 - Open questions and risk register

## 1. Decision policy

Unknowns are not filled with optimistic assumptions. Each is assigned to the earliest phase that can resolve it. A decision that changes public contracts, safety, data ownership, or product independence requires an ADR; a device/site calibration result does not.

## 2. Open questions

| ID | Question | Needed by | Resolution evidence | Default until resolved |
|---|---|---|---|---|
| Q-001 | What firmware/system versions and advertised APIs are on the user's R201? | P1 | Capability probe | Feature `unverified`/disabled |
| Q-002 | Which R2 sensor stream units/axes/rates are reliable on this firmware? | P1/P2 | Static and bounded-motion calibration | Preserve raw values; no world claims |
| Q-003 | What are measured stop latency/distance and safe speed curves on office surfaces? | P2 | Supervised calibration runs | Lowest bounded test envelope |
| Q-004 | Which USB microphone and audio output will be used on the Pi? | P3 | Device enumeration and benchmark | Simulator/file input |
| Q-005 | Does custom "Hey R2" wake detection meet office false-trigger goals? | R2 MVP | Labeled local corpus | Push-to-talk/alternate wake |
| Q-006 | Can Pi 4 run selected STT under simultaneous BLE/audio/web load? | R2 MVP | Latency/resource benchmark | Offload STT to Mac/LAN/remote |
| Q-007 | Which notification channel should deliver "show me" links? | Post-MVP integration | User choice and security review | PWA only |
| Q-008 | Which email provider/scopes and definition of priority are desired? | Information integration | User config and labeled examples | Mock/read-only adapter only |
| Q-009 | Which BSM host OS/hardware is the first reference deployment? | P4 | Host inventory/benchmark | Portable CPU implementation |
| Q-010 | Which fixed/shared-clock audio interface and microphones will form the reference array? | P5 | Hardware selection/calibration | Heterogeneous POC labeled coarse |
| Q-011 | Can the Pi-mounted probe speaker provide the needed bandwidth/timing stability safely? | P5 | Frequency/latency/SPL bench test | Stationary calibrated source |
| Q-012 | What microphone coordinates or array calibration fixture can be measured independently? | P5 | Ground-truth survey/calibration | Known synthetic array only |
| Q-013 | What office zones, stairs/drop-offs, people/pet patterns, and geofence apply? | First real Discovery/mapping | Operator walkthrough/config | Tiny supervised clear-area zone |
| Q-014 | What raw audio/transcript/email/map retention does the operator want? | P3/P5 | Explicit privacy configuration | Minimal/local/short retention |
| Q-015 | When can a BSM advisory influence patrol/Discovery rather than display only? | P7 | Repeated real-room validation and safety review | Display/advisory only |

## 3. Risk register

Scale: probability and impact are Low/Medium/High before mitigation.

| ID | Risk | P | I | Mitigation/gate | Trigger/indicator |
|---|---|---:|---:|---|---|
| R-001 | Unofficial `spherov2.py` breaks with current BlueZ/Bleak/Python or firmware | M | H | Pin/fork behind driver; P1 probe; simulator; TCP/packet evidence only as fallback research | connect/notify/command failures |
| R-002 | Multiple processes contend for BLE and destabilize R2 | M | H | Single BLE owner and IPC; process/port lock; conformance test | second connection/adapter instance |
| R-003 | Optional STT/model starves safety/ BLE on Pi | M | H | CPU/memory limits, lower priority, offload adapters, stop-load benchmark | latency/temp/backlog threshold |
| R-004 | Wake phrase false triggers initiate unwanted action | M | H | Wake only opens session; deterministic confirmation for motion; "R2" restricted; labeled benchmark | false accepts in office corpus |
| R-005 | Discovery collides before spatial system is trusted | H | M/H | Short low-speed supervised segments, physical geofence, collision stop; no prevention claim | repeated collisions/stuck |
| R-006 | R2 odometry drift contaminates BSM geometry | H | H | Separate `odom`/`world`, covariance, loop/held-out validation, provider transform | residuals/jumps grow |
| R-007 | Consumer device clocks/audio processing make ranging unusable | H | H | Measure/disclose; shared-clock array reference; degrade/abstain; phone results separate | offset/drift/AGC uncertainty |
| R-008 | Room echo inverse problem is underdetermined or produces false surfaces | H | H | Observability diagnosis, competing hypotheses, held-out emissions, uncertainty, unknown != free | inconsistent map/low coverage |
| R-009 | Onboard R2 sounds lack probe bandwidth/repeatable timing | H | M | Use independently controlled calibrated speaker; catalog onboard only | correlation/RIR poor |
| R-010 | Optional blueprint biases map toward incorrect layout | M | M | Treat as versioned uncertain prior; wrong-prior tests | evidence/prior residual conflict |
| R-011 | Provider/network loss leaves agent moving | L/M | H | Local lease/watchdog; fail-closed; INT-S04 in every mission state | heartbeat/session expiry |
| R-012 | Email/web content injects model instructions | H | H | Read-only isolated worker, untrusted labeling, no motor tools, adversarial tests | tool-like text in content |
| R-013 | Continuous microphones create privacy harm | M | H | Wake/window capture, visible state, local-first, retention/delete controls | recording outside armed window |
| R-014 | Existing LAMP server is disrupted by install/upgrade | M | H | Pre-install audit/backup, isolated venv/user/paths, Apache path, no implicit OS upgrade, rollback | port/package/config conflict |
| R-015 | Flash storage wear or disk exhaustion loses continuity/control availability | M | M/H | WAL/checkpoints, bounded logs/audio, disk thresholds, high-endurance/SSD, backups | write rate/free-space alert |
| R-016 | Protocol evolves before first live integration and embeds accidental assumptions | M | H | SimAgent/SimProvider profiles, 6DoF models, contract tests, versioning/ADRs | R2/BSM private fields appear |
| R-017 | Accuracy targets are mistaken for product guarantees | M | H | Evidence-category labels and operating envelopes in every report/release | unlabeled single-number claim |
| R-018 | Trademark/proprietary media redistribution creates legal concern | L/M | M | Unofficial notice, preserve licenses, do not extract/redistribute firmware/audio | bundled proprietary assets |
| R-019 | Agent pursuit/intercept feature creates people/pet safety risk | M | H | Observation-only until dedicated safety case; exclude people/animals by default | request targets live subject |
| R-020 | Charging modification damages battery or creates fire risk | L/M | H | No battery/docking modification in MVP; human USB connection/manual rules | self-dock hardware proposal |

## 4. Review cadence

- Review open questions and risk triggers at every phase gate.
- Update probability/impact only with evidence and retain history in Git.
- Any uncontrolled movement, battery/heat anomaly, unexpected recording, security event, or false-valid map is a stop condition and regression-test requirement.
- A new hardware type, provider, agent, external integration, or autonomy mode adds a focused hazard/threat review before implementation.

