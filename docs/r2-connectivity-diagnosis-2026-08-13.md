# R2 connectivity diagnosis — 2026-08-13

The connectivity fault is resolved for stationary read-only sessions.

## Root cause

Pinned `spherov2.py` 0.12.1 closes its Bleak adapter by awaiting
`BleakClient.disconnect()` before stopping and joining its non-daemon event-loop
thread. When BlueZ reports an already-gone connection, disconnect can raise
`EOFError`; the remaining cleanup never executes and the process hangs.

Separately, a command timeout followed by that close failure caused the cleanup
`EOFError` to overwrite the primary `TimeoutError`, incorrectly turning an
otherwise classifiable missing response into an opaque failure.

## Fix

- `Spherov2R2Driver.disconnect` preserves the first command failure and records
  cleanup failure separately.
- `ResilientBleakAdapter` delegates scan/connect/write/notify behavior to the
  pinned adapter but always stops and joins its worker thread in `finally`.
- An already-disconnected close error is tolerated only after the worker exits;
  a still-connected device or worker that fails to stop remains an error.
- Passive scanning is stopped before an exclusive R2 session and restored only
  after zero connections are confirmed.

## Hardware evidence

With the configured identity kept outside Git, release `18d52e9` passed:

- one exact-identity connect, full identity query, battery query, and clean
  disconnect in 17 seconds;
- five consecutive fresh connect/query/disconnect cycles, all passing;
- one persistent 30-minute stationary session with 30 battery samples and a
  clean disconnect.

Every diagnostic reported `movement_performed: false`. No motor, heading, head,
leg, LED, audio, or animation command was used. The Pi stayed near 37°C and the
final connection count was zero.

This resolves basic BLE connectivity and the Phase 1 five-cycle/30-minute
stationary link gates. It does not show that firmware acknowledges DID 22/CID 1:
the one authorized OFF/0 bench recorded a transmitted request but no matching
response. That command-specific result remains `stop_unconfirmed` after the
exception-precedence correction and must not be described as successful stop
acknowledgement.

## Stationary capability follow-up

One authorized stationary capability probe was attempted from release
`18d52e9`. The passive scanner was stopped for exclusive BLE ownership and
restored afterward. The probe terminated with `TimeoutError`, reported no
locomotion, and left the driver disconnected and stopped. The Pi reported
36.5 C after the run and both `r2-ble` and `r2-chat` were active.

The pre-fix failure artifact could not identify whether the timeout occurred
during connection, identity, battery, LED, head, audio, or stop. The probe now
wraps failures with a stable sanitized capability phase while preserving a
separate disconnect-cleanup error type. Tests cover a primary capability
timeout combined with a cleanup failure, ensure the primary phase wins, and
ensure private exception text is not persisted. No retry was performed.

The supervising operator subsequently reported no sound, LED activity, or
movement during the attempt. That observation proves the visible/audible
expression did not complete, but the pre-fix artifact is insufficient to
distinguish an early query timeout from a timeout on the first LED command.

A fresh preflight and one instrumented rerun isolated the failure to
`head.safe_range`: the R201 firmware did not acknowledge the read-only dome
position query before the client timeout. Identity, battery, and both halves of
the low-brightness LED preview completed before that phase. Audio was not
attempted. The run failed closed without retry, reported no locomotion, and
ended disconnected/stopped with both Pi services active. Until a different
reviewed strategy is available, the dome-position query is classified failed
for firmware `7.0.101`; audio remains untested, and LED protocol completion is
not a substitute for operator confirmation that light was visible.
