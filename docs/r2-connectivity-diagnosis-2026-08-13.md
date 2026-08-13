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
