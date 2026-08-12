# Stationary proof of life and R2 dashboard

## Scope

The proof-of-life command performs exactly one bounded, non-locomotive expression
and records a privacy-safe status report. It may read R2 identity, firmware,
battery, and head position; flash the logic-display LED bank twice at brightness
8; play one verified R2 sound at volume 8; and sweep the dome within ±20 degrees
before returning it to the original position. It never calls drive, heading,
legs, or stock animation primitives. The random choice is reproducible from the
seed saved in the report.

The command is disabled by default. A real run requires the stationary HIL flag,
all physical preflight confirmations, a second go confirmation, the external
`R2_PROOF_OF_LIFE_ARM_TOKEN`, and an externally supplied droid identity. Battery
state is checked after connection and an unknown, low, or critical state blocks
the expression. A durable, identity-free progress journal records each boundary
so an external watchdog can classify a timeout without assuming success.

The report distinguishes Pi CPU temperature from ambient temperature. Ambient
temperature remains `sensor_not_configured` unless a documented external sensor
is installed; no droid ambient temperature is inferred. Host values include OS,
kernel, architecture, Python, uptime, load, CPU count and temperature, throttle
flags, memory, disk, network-interface link state, clock sync, Apache/Bluetooth/
dashboard service state, audio-card inventory, and collector process state.
Droid values include model/firmware facts, firmware battery state and voltage,
head query result, connection, safe hold, selected expression/restoration claims,
and the invariant that locomotion was not performed.

## Dashboard

The progressively enhanced PWA is served at `https://raspberrypi.local/R2D2/`.
It is portrait-first for iPhone and uses an original brushed-metal, orange/amber
astromech-console design based on the operator's layout sketch. It provides:

- a local text dialogue with visible R2 binary and Basic translation;
- deterministic offline replies for greeting, status, battery, issue, and latest
  proof-of-life questions;
- animated annunciators and decorative waveforms that do not imply telemetry;
- live ten-second privacy-safe Pi and last-observed R2 status snapshots;
- prominent issue highlighting and measurement timestamp;
- a static guarantee that the page exposes no drive or proof-of-life endpoint.

The service worker caches only versioned static assets. It never caches
`status.json`, emergency state, or authenticated API data. The first deployment
is read-only and restricted by Apache to loopback/private-LAN addresses. It does
not yet satisfy the full authenticated P2 operator-control requirement in
R2-012: emergency stop, deadman manual controls, authentication, and a live
reasoning service remain future gates. The dialogue fallback runs locally in the
browser and cannot issue physical commands.

## Deployment model

Apache serves release-owned static assets and the generated status file. A
host-native, sandboxed `systemd` oneshot/timer refreshes the status every ten
seconds as `www-data`; its writable scope is limited to
`/var/lib/r2-runtime/dashboard`. The release is staged under
`/opt/r2-runtime/releases/<revision>` and activated through the
`/opt/r2-runtime/current` symlink so rollback does not require modifying files in
place. Apache configuration is syntax-checked before reload.

The development simulation is:

```text
python scripts/tasks.py proof-of-life-sim
```

The HIL entry point intentionally is not documented as a copy-paste convenience
command. Use the reviewed Pi launcher only for one explicitly authorized run,
under a bounded external watchdog, and preserve its immutable JSON output and
progress journal. Never retry automatically after a timeout or physical anomaly.

## First deployment and HIL attempt

Commits `eda49e6`, `7adeab4`, and the private-IPv6 allowlist correction
`7ba7239` were deployed as immutable releases on 2026-08-12. Apache syntax,
`/R2D2` redirect, hardened `/R2D2/` response, uncached status response, timer,
and rollback directory all passed target-host checks. The active release is
`7ba7239`; `7adeab4` remains available for rollback.

The one authorized proof-of-life attempt used the exact `7adeab4` HIL staging.
It connected, read identity, and passed the battery gate. Ten seconds later the
journal recorded `session_failed` before either `head_checked` or
`expression_started`, so no LED flash, sound, dome-set, drive, heading, leg, or
animation primitive was issued. The child reported `EOFError` and software state
`offline`/safe-held, but no `disconnect_completed` marker was written. The
75-second external watchdog terminated the lingering process. Bluetooth was then
powered off; no connection or HIL process remained. There was no retry. Direct
operator observation subsequently confirmed that no sound, dome movement, or
LED activity occurred; the base, legs, heading, and location did not change; and
R2 ended stationary, silent, with all LEDs off. The attempt remains a failed HIL
cycle because the intended expression was not performed and disconnect
completion was not journaled.
