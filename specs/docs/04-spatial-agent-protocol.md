# 04 - Spatial Agent Protocol (SAP)

Protocol version: **0.1.0 draft**

## 1. Purpose

SAP is a versioned application protocol between a **Mobile Agent** and a **Spatial Provider**. It defines capabilities, commands, observations, events, coordinate/time semantics, artifacts, failures, compatibility, and conformance tests.

SAP deliberately does not define BLE packets, robot drivers, mapping algorithms, database schemas, user interfaces, or a required message broker.

## 2. Roles

### Mobile Agent server

Implements a generic Agent API and event stream. R2 Runtime is the first implementation.

### Spatial Provider server

Implements a Spatial Provider API and event stream. BSM is the first implementation.

### Integration session

A logical, authenticated relationship binding one provider, one or more agents, compatible protocol/capabilities, coordinate/time declarations, and an expiration. Either side may reject or terminate a session.

## 3. Versioning

- Protocol versions use Semantic Versioning.
- Before `1.0.0`, minor versions may change, but implementations still declare compatibility explicitly.
- After `1.0.0`, additive optional fields/events are minor changes; removals or semantic changes require a major version.
- Messages include `schema_version`.
- HTTP responses include `SAP-Version` and may include `SAP-Supported-Versions`.
- Consumers ignore unknown additive fields and event types unless strict safety policy requires rejection.
- Capability negotiation selects one mutually supported version and feature set.

## 4. Identity

Stable IDs are opaque strings or URNs, for example:

```text
urn:sap:agent:home:r2-d2-01
urn:sap:provider:home:bsm-01
urn:sap:node:office:mic-array-01
urn:sap:frame:office:world
```

Display names are never identity. IDs cannot embed secrets, MAC addresses intended to remain private, or mutable room labels.

## 5. Event envelope

Every event uses this logical envelope:

```json
{
  "schema_version": "0.1.0",
  "event_id": "0198...",
  "event_type": "agent.pose.observed",
  "producer_id": "urn:sap:agent:home:r2-d2-01",
  "session_id": "0198...",
  "correlation_id": "0198...",
  "causation_id": "0198...",
  "sequence": 1042,
  "occurred_at": "2026-08-11T18:00:00.123456Z",
  "monotonic_ns": 9912345678,
  "clock": {
    "clock_id": "r2-pi-monotonic-boot-abc",
    "sync_source": "ntp",
    "uncertainty_ms": 2.4,
    "drift_ppm": 8.0
  },
  "payload": {}
}
```

`sequence` is monotonically increasing within a producer stream/epoch. Consumers resume SSE with the last event ID and tolerate duplicates. Event IDs should use UUIDv7 where available.

## 6. Common data rules

### 6.1 Units

- distance/position: meters;
- time/duration: seconds, except explicit integer nanoseconds/milliseconds fields;
- linear velocity: meters/second;
- angles/orientation: radians and unit quaternions;
- angular velocity: radians/second;
- frequency: hertz;
- sample rate: integer samples/second;
- temperature: degrees Celsius;
- sound pressure: dB with an explicit reference/weighting such as dB SPL or dBA.

Fields include unit suffixes where ambiguity is plausible. UI adapters may display other units.

### 6.2 Pose

A pose includes:

- `frame_id` and optional child frame;
- position `x_m`, `y_m`, `z_m`;
- normalized quaternion `x`, `y`, `z`, `w`;
- optional linear/angular velocity;
- row-major 6x6 covariance or a documented reduced uncertainty;
- confidence from 0 to 1;
- source/provenance and validity interval;
- measurement time/clock quality.

A covariance of zero means known exactly only in simulation/fixture truth. Unknown uncertainty is `null`, never zero.

### 6.3 Geometry

Public geometry is right-handed. `z` is up in the world frame. Frame transforms are time-indexed and form a graph. A consumer must reject cycles, missing frame paths, invalid quaternions, incompatible map revisions, and stale transforms.

### 6.4 Confidence and status

Every estimate declares both status and numerical uncertainty when possible:

- `unknown`
- `unverified`
- `degraded`
- `valid`
- `invalid`
- `expired`

Confidence is not a replacement for covariance or an operating-envelope statement.

## 7. Capability discovery

Both roles expose `GET /v1/capabilities`. A response includes:

- product, build, protocol versions, and role;
- supported commands/events/media types/transports;
- coordinate frames and transform support;
- timing sources and typical uncertainty;
- movement/footprint/speed/probe limits for agents;
- map/advisory/solver capabilities for providers;
- security and artifact-upload capabilities;
- feature verification state.

Capabilities are session snapshots. A `system.capabilities.changed` event invalidates affected assumptions.

## 8. Session negotiation

`POST /v1/sessions` proposes:

- peer identity and callback/event endpoint where used;
- protocol versions;
- required/optional capabilities;
- requested operating mode and duration;
- world/odom/frame declarations;
- clock/synchronization declarations;
- authentication subject and policy profile;
- requested artifact/retention behavior.

The response returns accepted version/features, session ID, expiry, policy/safety limits, event cursor, and rejected requirements. A session never grants authority beyond the agent's local safety policy.

## 9. Agent API

Normative paths are detailed in `contracts/agent-api.openapi.yaml`.

| Method/path | Purpose |
|---|---|
| `GET /v1/health` | Liveness/readiness and degraded components |
| `GET /v1/capabilities` | Agent capability snapshot |
| `POST /v1/sessions` | Negotiate integration session |
| `DELETE /v1/sessions/{id}` | End session; active mission safely cancels/holds |
| `POST /v1/commands` | Submit high-level idempotent command |
| `GET /v1/commands/{id}` | Command state/result |
| `POST /v1/commands/{id}/cancel` | Request cancellation/safe hold |
| `GET /v1/events` | Resumable SSE stream |
| `GET /v1/transforms` | Query agent-known transforms/uncertainty |

Required command types:

- `stop`
- `safe_hold`
- `move_relative`
- `rotate_to`
- `navigate_to`
- `hold_pose`
- `emit_acoustic_probe`
- `set_mode`
- `look_toward`
- `express`

An implementation may advertise only a safe subset. `stop` and `safe_hold` are required for a movable agent.

## 10. Spatial Provider API

Normative paths are detailed in `contracts/spatial-provider-api.openapi.yaml`.

| Method/path | Purpose |
|---|---|
| `GET /v1/health` | Liveness/readiness and degraded components |
| `GET /v1/capabilities` | Provider capability snapshot |
| `POST /v1/sessions` | Negotiate integration session |
| `DELETE /v1/sessions/{id}` | End provider session |
| `POST /v1/observations` | Submit normalized agent/node observation metadata |
| `POST /v1/route-requests` | Request route/hazard advisory |
| `GET /v1/localization/{agent_id}` | Latest valid localization estimate |
| `GET /v1/maps/{map_id}/revisions/{revision}` | Map revision metadata/artifacts |
| `GET /v1/features/{feature_id}` | Feature/uncertainty/evidence metadata |
| `GET /v1/events` | Resumable SSE stream |

Bulk recordings use a bounded multipart artifact endpoint or an accepted content-addressed URI; they are not embedded as base64 in normal events.

## 11. Command lifecycle

Commands include:

- command ID and idempotency key;
- type and typed parameters;
- requested execution/deadline;
- correlation/causation IDs;
- session/controller identity;
- preconditions such as pose/map/capability/safety revision;
- requested bounds;
- dry-run flag where supported.

Lifecycle:

```text
received -> accepted | rejected
accepted -> queued -> running -> succeeded | failed | canceled | timed_out
```

HTTP acceptance does not mean physical completion. Terminal events and `GET` state are authoritative. Repeating an idempotency key returns the original command/result. A command older than its deadline is rejected without actuation.

## 12. Required events

### Agent events

- `agent.state.changed`
- `agent.pose.observed`
- `agent.motion.observed`
- `agent.health.changed`
- `agent.collision.detected`
- `agent.stuck.suspected`
- `agent.command.accepted|rejected|started|progress|completed|failed|canceled`
- `agent.probe.emitted`
- `agent.mode.changed`
- `agent.tag.created|updated`

### Spatial events

- `spatial.localization.estimated`
- `spatial.transform.estimated`
- `spatial.map.revision.published`
- `spatial.feature.detected|updated`
- `spatial.hazard.detected|cleared`
- `spatial.route.advisory.created|expired`
- `spatial.observability.degraded`

### Common system events

- `system.health.changed`
- `system.clock.quality.changed`
- `system.capabilities.changed`
- `system.session.expiring|ended`
- `artifact.available|expired`

## 13. Acoustic probe event

`agent.probe.emitted` includes:

- source/probe/waveform IDs and waveform hash;
- requested and actual gain;
- sample rate and intended bandwidth;
- actual start wall/monotonic time and uncertainty;
- emission duration/repetition index;
- source pose/transform and uncertainty at emission;
- clipping/fault status;
- correlated capture/mission IDs.

If actual emission timing cannot be measured, the field states that limitation. Requested time cannot be substituted as actual time.

## 14. Route/hazard advisory

An advisory includes:

- advisory ID, map revision, frame, creation/expiry;
- target and agent footprint/dynamics assumptions;
- path/corridor/hazard geometry;
- clearance, recommended speed cap, and confidence;
- evidence/provenance and unsupported regions;
- reason codes and alternative/stop recommendation.

The agent may accept, modify, or reject it. Acceptance still requires a local motion lease.

## 15. Artifacts

Artifact metadata contains:

- artifact ID and media type;
- size and SHA-256 hash;
- immutable creation time and producer;
- measurement/event/map/calibration links;
- retention/expiry and authorization scope;
- retrievable URI or upload receipt.

URIs may be short-lived. Stable references use artifact IDs/hashes. Clients verify hashes before processing.

## 16. Errors

Errors use RFC 9457-style problem details with stable SAP codes, for example:

- `sap.protocol_version_unsupported`
- `sap.capability_missing`
- `sap.session_expired`
- `sap.command_stale`
- `sap.command_unsafe`
- `sap.frame_unknown`
- `sap.map_revision_stale`
- `sap.clock_uncertainty_excessive`
- `sap.observability_insufficient`
- `sap.artifact_hash_mismatch`
- `sap.rate_limited`

Free text aids humans but is never the only machine signal.

## 17. Security

- All non-loopback production traffic uses TLS.
- Development bearer tokens are scoped to role/session and stored outside source control.
- mTLS is the preferred profile for persistent LAN devices.
- Command endpoints enforce authentication, authorization, replay/idempotency, rate, size, and deadline limits.
- Artifact access is least-privilege and time-bounded.
- Peer-provided text, filenames, map labels, transcripts, and metadata are untrusted.
- A provider cannot acquire raw-motor or arbitrary-code authority through capability negotiation.

## 18. Conformance

The `protocol` project supplies:

- JSON Schema/OpenAPI validation;
- canonical valid and invalid examples;
- generated client compatibility tests;
- agent/provider simulators;
- duplicate/out-of-order/stale/reconnect event tests;
- time/frame/unit/covariance validation;
- command idempotency and lifecycle tests;
- capability negotiation matrix;
- a protocol changelog.

A product is SAP-conformant only for a declared role, version, feature profile, and test-suite build. Conformance does not imply acoustic accuracy or physical safety certification.

