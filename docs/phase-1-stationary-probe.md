# Phase 1 stationary capability-probe slice

## Outcome and scope

This slice adds the owned `Spherov2R2Driver` boundary, a single serialized BLE
owner state machine, deterministic stationary capability probing, immutable
evidence recording/replay, and a simulation scenario covering five
connect/probe/disconnect cycles plus a virtual 30-minute stationary soak.

The adapter lazily targets the external `spherov2.py` 0.12.1 package and cannot
address a device unless the separate hardware profile is installed. Its PyPI
source archive was verified at SHA-256
`087929a28164af78c8a258396593a51d45fc89af23e86c524d86d0a5d094908f`.
Bleak 0.21.1 is selected as the Python 3.11 compatibility baseline. The complete
CPython 3.11 Linux/aarch64 wheel set is recorded in
`r2-runtime/requirements-hardware-pi.lock` and
`r2-runtime/hardware-wheelhouse.manifest.json`; all six downloaded wheel hashes
were verified. This is resolver evidence, not proof of imports, BlueZ behavior,
or BLE operation on the target Pi.

The resolver ran on Windows, whose environment-marker handling incorrectly
selected `bleak-winrt` even with a cross-platform pip target. The checked Pi
manifest therefore resolves Bleak 0.21.1's published Linux branch explicitly:
`dbus-fast>=1.83.0,<3` and `typing-extensions>=4.7.0` for Python 3.11. The
verifier rejects Windows-only artifacts. Run
`python scripts/verify_hardware_lock.py --wheelhouse <directory>` before moving
the wheelhouse to a Pi; installation and target imports remain a separate gate.
After installing from the verified offline wheelhouse, run
`python scripts/verify_hardware_imports.py` on the Pi. It refuses any host other
than Python 3.11 on Linux/aarch64, checks every installed version against the
lock, and imports modules only. It does not scan BLE or construct a backend.

Target-host verification completed on 2026-08-11 using Python 3.11.2 on Debian
13/aarch64. The Pi's default `python3` is 3.13.5, so deployment must explicitly
select Python 3.11. The host lacks `python3.11-venv`; verification therefore used
an isolated temporary `pip --target` directory with `--no-index` and
`--require-hashes`, followed by `python3.11 -S`. All six exact versions imported
from that directory. BLE was not scanned or accessed, and this is not R2 HIL.

A subsequent read-only host readiness audit found BlueZ 5.82 active, system
D-Bus available, NTP synchronized, and sufficient temporary storage. The local
Bluetooth controller was powered off, non-pairable, and non-discovering; it was
not powered on or scanned. The measured 35.537 °C value is Pi CPU temperature
only. It is not ambient temperature and is not a droid sensor reading.

## Stationary HIL discovery attempt 1

On 2026-08-11 the operator authorized R2 access while charging with a hard
constraint against changing heading, direction, or location. The Pi controller
was software-blocked; the existing `rfkill` utility safely unblocked it and the
controller came up non-pairable and non-discovering. A 10-second R2-prefix scan
and a 15-second name-filtered scan found no R2/Sphero advertisement. R2 was never
connected or commanded. The controller was returned to its original powered-off,
software-blocked state and all temporary files were removed. No device address
is stored in repository evidence. Testing is blocked until R2 advertises while
remaining on charge and stationary.

On the second attempt, one R2-D2 advertisement and one BB-8 advertisement were
classified correctly by the pinned library. This verifies that the discovery
filter distinguishes the in-scope R2 from the out-of-scope BB-8. Neither device
was connected or commanded. Advertised names remain external configuration and
are not persisted in repository evidence.

## Simulation

Run `python scripts/tasks.py p1-sim` (or `make p1-sim`). Output includes seed
`20260811`, five content hashes, 1,800 seconds of virtual stationary soak, 31
health samples, zero movement, and final `safe_hold`.

The capability report never stores the configured BLE identity. It derives a
non-secret device reference from public model/system fields. Movement, stop
latency, and locator calibration remain `untested` because they require
separately authorized motion HIL.

## HIL entry point

`python scripts/hil_stationary_probe.py --output <new-file>` is separately
marked and disabled by default. It requires explicit authorization, operator
presence, device inspection, temperature confirmation, one-meter keep-out, an
emergency-stop path, and identity supplied through `R2_DEVICE_IDENTITY`. LED,
head query, and quiet audio preview require separate flags; audio additionally
requires an explicit verified ID. This command has no movement option. A future
movement command must be separate and require the full motion preflight.

## Failure and recovery behavior

- Missing backend or wrong library version fails closed.
- Connection failure returns the owner to `offline` with stopped state.
- Disconnect and link loss invalidate motion state and do not auto-resume.
- Every normal disconnect issues stop first.
- Low/critical/unknown battery blocks optional physical probe actions.
- Existing evidence files cannot be mutated; replay verifies SHA-256.

## Rollback

Remove the Phase 1 modules and task entry point. There are no migrations,
services, credentials, network calls, or device changes to reverse.
