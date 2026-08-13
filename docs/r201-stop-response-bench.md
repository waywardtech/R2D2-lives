# R201 stop-response stationary bench procedure

Status: procedure only; execution is not authorized.

## Purpose

Determine whether R201 firmware `7.0.101` acknowledges drive DID 22 stop
commands when the droid is not charging, without changing heading, direction, or
location. This procedure characterizes protocol behavior only. It does not pass
the Phase 1 movement gate and must not be run from automated tests or CI.

## Hard prerequisites

The operator must explicitly authorize this exact bench test immediately before
execution and remain present throughout. Stop if any item cannot be confirmed:

- exact configured R2 identity is supplied outside source control;
- R2 is unplugged from USB charging and its battery state is safe;
- R2 and cable show no heat, swelling, leakage, or other damage;
- ambient conditions are within the manual's 0-40 C envelope;
- the droid is visible and physically contained so wheel activity cannot change
  heading, direction, or location;
- people and animals remain at least one meter away;
- Pi/R2 BLE health and the Pi watchdog are confirmed;
- a manufacturer-supported physical shutdown method is identified, reachable,
  and demonstrated while stationary before any drive DID is transmitted;
- the operator has approved the exact single-command limit and abort plan.

A software command over the same BLE connection is not an independent shutdown
method. A cradle or restraint limits location but is not proof that motors have
stopped. Until the physical shutdown method is identified and demonstrated, the
drive-command portion is blocked.

## Privacy-safe capture design

Instrument the owned library boundary, not BlueZ discovery output. Capture only:

- UTC and monotonic timestamps with clock identity, synchronization source, and
  uncertainty;
- direction (`tx` or `rx`), DID, CID, sequence, flags, decoded error, byte count,
  and a SHA-256 of the encoded packet;
- connection/owner state transitions and terminal cleanup outcome.

Do not capture or persist BLE addresses, advertised names, configured identity,
credentials, hostnames, unrelated notifications, or arbitrary packet payloads.
Keep any temporary byte-level trace outside the repository and remove it from the
Pi after deriving and independently reviewing the sanitized artifact.

`r2_runtime.packet_trace.StopResponseTraceRecorder` implements the sanitized
artifact boundary in simulation. It accepts only DID 22/CID 1, prohibits a
second transmitted command, retains packet length and SHA-256 rather than bytes,
requires opaque session/clock identities, correlates the response sequence, and
uses the finite protocol-v2 error vocabulary. The recorder alone does not
authorize or execute this procedure.

`TracedRawMotorOffExecutor` now provides the reviewed, opt-in vendor seam. The
normal backend still uses the public `drive_control.set_raw_motors` path. Only an
explicitly constructed executor calls the pinned `Drive._encode`/`toy._execute`
pair, observes the encoded command before dispatch and the returned response
afterward, and leaves the original flags, synchronous timeout, and error behavior
unchanged. The seam has fake-vendor simulation coverage but is not wired into an
operator command.

The separately marked runner is `scripts/hil_stop_response_bench.py`. Its default
invocation exits before constructing the backend. It requires every physical
preflight flag, an external exact arm token, synchronized clock source and
bounded uncertainty, opaque boot-clock/session identities, and an interactive
post-disconnect `PHYSICAL_NORMAL` confirmation. It queries battery state, then
relies on the owner's single normal disconnect stop; the driver prevents a retry
after timeout. Any earlier exception, unsafe battery, remaining Bluetooth
connection, missing physical confirmation, or non-success response exits failed.
An operator-confirmed `TimeoutError` remains valid failed evidence classified as
`stop_unconfirmed`; it is not relabeled as invalid or promoted to success.
The connect/battery/disconnect-stop sequence lives in
`r2_runtime.stop_bench.run_stop_bench_session` and has deterministic coverage for
normal, timeout, unsafe-battery, and battery-query-failure paths. Each connected
path asserts exactly one stop attempt and terminal BLE disconnect.

The supplied R201 product manual does not document an app-independent physical
power cutoff. Do not substitute instructions for unrelated R2-D2 products. The
operator's emergency path and physical containment must therefore be reviewed
for this exact R201 setup before authorizing the runner.

## Staged execution

1. Re-run the full simulation and recorder/replay tests. Confirm the repository
   is clean and record the commit under test.
2. Copy a hash-verified, minimal source bundle to a new Pi temporary directory.
   Do not install a service or change boot configuration.
3. Restore the Bluetooth controller's prior state, then run one read-only identity
   query through the capture boundary. This proves TX/RX correlation without a
   drive command. Abort on any unexpected device or response.
4. Disconnect, verify the droid remains normal, and review the sanitized trace.
5. Only after a second explicit go/no-go confirmation, connect once and transmit
   exactly one raw-motor command: left `OFF/0`, right `OFF/0`. Do not send a
   heading-bearing roll command, retry, LED/audio/animation action, or any
   non-zero motor value.
6. Wait only for the bounded response window. Record a matching response, an
   explicit firmware error, or a timeout. A successful write without a matching
   response remains `stop_unconfirmed`.
7. Disconnect once. If disconnect or motor state is uncertain, use the previously
   demonstrated physical shutdown method. Do not send another motor command.
8. Verify R2's physical state, confirm zero BLE connections, restore the
   controller's prior power/rfkill state, remove the Pi temporary directory, and
   scan the proposed artifact for private identity data before committing it.

## Abort conditions

Abort immediately on unexpected wheel/head/leg movement, sound or LED behavior,
wrong identity, battery/thermal anomaly, BLE ambiguity, operator loss, keep-out
violation, watchdog failure, malformed/unrelated response, timeout, or cleanup
failure. A failed or timed-out stage ends the hardware sequence without retry.

## Result classification

- `acknowledged_success`: matching DID/CID/sequence response with firmware
  success, followed by verified disconnect and normal physical state.
- `acknowledged_error`: matching response with a firmware error.
- `stop_unconfirmed`: write observed but no valid matching response in the
  bounded window.
- `invalid_test`: any identity, clock, capture, preflight, or cleanup invariant
  was not satisfied.

Only `acknowledged_success` resolves the response-path question. It still does
not establish moving stop latency, stopping distance, or collision prevention.

## Deterministic trace matrix

`python scripts/tasks.py stop-trace-sim` exercises the complete evidence
classifier without importing Bluetooth or vendor hardware modules. Seed
`20260811` produces stable cases for acknowledged success, an acknowledged
firmware error, response timeout, cleanup failure, and response-sequence
mismatch. Timeout remains `stop_unconfirmed`, cleanup failure remains
`invalid_test`, and mismatched evidence is rejected rather than interpreted.
The output explicitly reports `hardware_accessed: false` and
`movement_performed: false`. This closes the simulation classifier gate only;
firmware behavior still requires the separately authorized physical bench.
