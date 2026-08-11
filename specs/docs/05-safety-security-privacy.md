# 05 - Safety, security, and privacy

## 1. Safety posture

This is a mobile physical system with microphones, network access, and optional model-driven behavior. Safety is an architectural property, not a prompt instruction. The deterministic R2 safety executive is the only authority that can approve actuation.

The supplied R201 manual is normative for physical handling. Its constraints include visible operation, approximately one meter between R2 and people, operation/storage from 0 to 40 C, inspection for damage, avoidance of hazardous/public areas, and careful supervised charging.

## 2. Safety invariants

The following must be true in all modes:

1. No motion without a valid local lease.
2. Stop/safe-hold does not require internet, LLM, BSM, email, or PWA availability.
3. Loss of the commanding process, session, lease, BLE link, or required localization cannot continue or resume prior motion.
4. Startup/restart begins stopped; command state is not reconstructed into movement.
5. Every motion has configured speed, duration, distance, and spatial bounds.
6. Commands outside calibrated capability are rejected, not clipped silently unless policy explicitly records the modification.
7. Spatial estimates and advisories expire and include uncertainty; stale/unknown data cannot authorize motion.
8. Collision detection triggers stop and assessment. It is not described as prevention.
9. Model/email/web content cannot bypass typed tools and safety validation.
10. Automated tests cannot address real motors unless an explicit bounded hardware profile is enabled locally.

## 3. Hazard analysis

| Hazard | Primary cause | Required controls | Safe failure |
|---|---|---|---|
| Uncontrolled motion | hung process, stale command, reconnect resume | lease/watchdog, idempotency, deadline, single BLE owner | stop; invalidate lease |
| Person/pet contact | blind movement, wrong localization | manual one-meter keep-out, supervised envelope, speed/distance caps, geofence | stop/alert; no automatic pursuit |
| Furniture/wall collision | Discovery without validated map | short low-speed segments, collision/stuck detection, operator visibility | stop; cautious retreat only if assessed safe |
| Stair/drop-off | map absent or microphone ambiguity | physical test geofence/barrier; no unsupervised edge operation | stop before risk zone; manual recovery |
| Tip/fall/unsafe stance | uneven surface or aggressive turn | tilt/gyro thresholds, stance-aware limits | stop motors and alert |
| Low/critical battery | inaccurate estimate or ignored alert | verified state/voltage thresholds, hysteresis, mode restrictions | safe hold; charging staging |
| Heat/damaged battery | charging/use outside manual | external inspection, 0-40 C envelope, no unattended charging | power down/alert; human inspection |
| Excessive probe sound | gain/duty error | calibrated source, maximum level, quiet hours, operator arming | cancel emission; disable source |
| False confidence in map | simulation-to-real transfer, poor sync | uncertainty, validation, held-out checks, operating envelope | advisory-only/degraded state |
| Stale transform | clock/network delay | validity windows, map revision, monotonic time, jump checks | reject estimate/hold |
| Malicious content | prompt injection in email/web/transcript | untrusted-data boundary, read-only worker, tool allowlist | summarize/flag only |
| Unauthorized control | leaked token/spoofed peer | TLS, scoped auth, mTLS, audit, rate/replay limits | deny and alert |
| Privacy intrusion | continuous microphones or retained email/audio | wake/VAD, visible indicator, local-first retention, access controls | stop capture/delete per policy |

## 4. Movement safety envelope

Before real locomotion, the hardware calibration records:

- normalized command to measured speed curve;
- stopping distance and time by surface/battery;
- heading/turn error;
- locator drift by distance/turn;
- collision detection sensitivity;
- stance-specific limits;
- BLE command/stop latency distribution.

Initial configuration is conservative until measured. The reference first-motion test is a clear floor, low speed, no more than 0.25 m commanded travel, and an operator beside a tested stop control. Exact production caps are calibration outputs, not guessed constants in code.

### 4.1 Deadman behavior

Manual joystick/continuous movement requires heartbeats. Releasing the UI, losing focus, losing network, or exceeding the heartbeat interval stops the droid. A single `move_relative` request is independently bounded and cannot be extended by delayed retries.

### 4.2 Stop paths

- Optional normally closed GPIO emergency button
- Local keyboard/operator command
- PWA emergency control
- Voice stop within an open listening session
- Watchdog/lease expiry
- Automatic safety triggers

All stop paths converge on the same idempotent `safe_hold` transition. Repeated stops are harmless.

## 5. Mode-specific constraints

### Discovery

Supervised only during MVP; short segments; low speed; clear geofence; stop after repeated encounters or confidence loss.

### Patrol

Requires an approved route version, localization threshold, abort points, and operator-configured schedule. A changed room invalidates route approval until reviewed.

### Mapping Mission

Requires operator arming, agent and microphone readiness, sound limits, hold confirmation before capture, and a safe motion plan. BSM cannot broaden R2 limits.

### Charging Staging

R2 stops at a verified point and requests human connection. The stock R201 USB cable is not automatically connected. Charging is not unattended and follows the manual.

## 6. Acoustic safety

- Begin calibration/probes at low output.
- Measure sound level at expected operator distance before automated sequences.
- Default to audible broadband signals compatible with actual hardware; do not assume phones support ultrasonic capture.
- Configure maximum gain, duration, repetition, duty cycle, and quiet hours at the R2/source and BSM mission levels; the lower limit wins.
- Avoid repeated startling sounds near people/animals and protect hearing.
- Log requested and actual source settings and cancel on clipping/fault.
- Do not use acoustic probes as covert surveillance; capture windows are explicit and indicated.

## 7. Security architecture

### 7.1 Trust zones

- **Physical control zone:** R2 BLE owner, safety core, optional GPIO; highest trust.
- **Local service zone:** authenticated Pi services and BSM on trusted LAN.
- **User interface zone:** browser/PWA; authenticated but exposed to web risks.
- **External information/model zone:** email, headlines, remote inference; untrusted input/output.
- **Artifact zone:** recordings/maps/transcripts; sensitive stored data.

Authority only decreases toward external zones. No externally supplied content is executable policy.

### 7.2 Authentication and authorization

- Loopback IPC uses OS permissions and service identities.
- LAN APIs use TLS and scoped tokens during development; persistent devices should use mTLS.
- Separate scopes include `agent.read`, `agent.command.safe`, `agent.mission`, `spatial.read`, `spatial.observe`, and `artifact.read/write`.
- `stop` may be broadly available to authenticated local operators, but never unauthenticated over a network.
- Raw diagnostic/motor/packet operations require a separate disabled-by-default local profile.
- Sessions, tokens, and artifact links expire and are auditable.

### 7.3 API defenses

- typed schema validation and bounded request sizes;
- deadlines, nonces/idempotency, rate limits, and replay detection;
- safe parsing of filenames/media and content-hash verification;
- SSRF prevention for artifact/email links;
- no arbitrary shell/file paths in public API;
- safe error messages without tokens, environment, or email content;
- dependency pinning, SBOM, vulnerability scanning, and signed/reproducible release artifacts where practical.

## 8. Agent and prompt-injection safety

`smolagents` or any replacement has only a small allowlist of typed high-level tools. It cannot:

- call BLE/raw motor APIs;
- acquire/extend a motion lease;
- change safety configuration;
- read secrets;
- execute shell code;
- treat email, webpages, transcripts, or map labels as instructions;
- follow arbitrary links;
- send/delete email in MVP.

Tool output is validated and passed through policy. The runtime clearly labels untrusted content in model context. Safety decisions are not delegated to natural-language reasoning.

## 9. Email and external information

- OAuth2 with read-only, least-privilege scopes
- Token storage outside repository and logs
- Sanitized metadata/preview extraction in an isolated worker
- No motor tools in that worker
- Message IDs referenced through opaque internal IDs
- Priority classification records model/rule version and confidence
- Rate limits, quiet hours, sender allow/block policy, and duplicate suppression
- "Show me" produces an authenticated view/link; it does not execute message content

## 10. Privacy

### 10.1 Microphones

- Wake/VAD processing local by default
- Visible UI/LED state for listening and active recording
- BSM capture uses explicit mission windows
- Raw continuous audio disabled by default
- Configurable pre-roll/post-roll kept minimal
- No speaker biometric identification in MVP
- R2 playback/probe intervals marked so they can be suppressed from speaker attention

### 10.2 Data classes

| Class | Examples | Default handling |
|---|---|---|
| Operational | health, command result, protocol version | retained for diagnostics with rotation |
| Spatial | maps, poses, named locations | local access-controlled; backed up if enabled |
| Audio | wake clips, mapping recordings | short configurable retention; encryption at rest recommended |
| Conversation | transcripts, summaries, tags | local, user-reviewable and deletable |
| External content | email subject/preview, headlines | minimal cached metadata; no body by default |
| Secrets | OAuth tokens, TLS keys | credential store, never continuity/log DB |

### 10.3 Retention and deletion

Retention is configured by class and purpose. Deletion must remove or cryptographically expire content and record a non-sensitive tombstone if audit continuity requires it. Derived maps must disclose when their underlying recordings were deleted.

## 11. Incident response

An incident bundle contains build/config hashes, service health, command/event audit, protocol session, relevant calibration IDs, and redacted logs. It excludes raw email/audio unless the operator explicitly includes them.

After uncontrolled motion, collision, unexpected sound level, authentication anomaly, or suspected battery damage:

1. safe hold/power isolation as appropriate;
2. prevent automatic restart of the affected mode;
3. preserve redacted evidence;
4. inspect physical hardware and environment;
5. reproduce in simulation/replay where possible;
6. add a regression/fault test before re-enabling.

## 12. Operator preflight for real movement

- R2 visually undamaged and within temperature range
- Clear, level, bounded floor; stairs/drop-offs blocked
- People/animals outside one-meter keep-out
- Battery and BLE healthy
- Correct droid identity and capability profile
- Emergency stop tested while stationary
- Speed/distance/duration/geofence shown and accepted
- Required localization/advisory fresh enough for the selected mode
- Microphone/probe level and privacy indicator verified when mapping
- Operator remains present and able to stop

