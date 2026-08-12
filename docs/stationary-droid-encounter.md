# Stationary nearby-droid encounter

## Scope

This feature lets R2 notice supported Sphero droid advertisements and perform a
short spectator-friendly reaction without changing base heading, direction,
location, stance, or leg position. Detection retains only the public droid class
(`bb8`, `bb9e`, `r2d2`, or `r2q5`). Advertised names, BLE addresses, and MAC
addresses are neither returned by the adapter nor written to evidence.

The interaction path sends a sanitized encounter to the owned
`ReasoningDispatcher` seam when configured. A dispatcher may select only a
semantic meaning: greeting, curiosity, excitement, or uncertainty. It cannot
select an audio ID, head angle, LED value, animation, motor value, or movement.
Failure or invalid output uses a deterministic local fallback.

## Charging-safe expression envelope

The deterministic compiler selects from reviewed R2-only enum names in the
pinned `spherov2.py` 0.12.1 catalog:

- `R2_HEY_*`, `R2_CHATTY_*`, `R2_POSITIVE_*`, `R2_EXCITED_*`, and `R2_LAUGH_*`;
- logic-display brightness at most 8/255;
- audio volume 8/255 for at most 1.25 seconds;
- dome positions bounded to ±20 degrees and ending at neutral;
- no immediate audio repetition.

The backend restores the prior audio volume and head position, turns the logic
display preview off, and stops audio even after an expression failure. Battery
state is checked first. Unknown, low, or critical battery blocks every reaction.

Full stock animation IDs are deliberately excluded. The reviewed upstream
0.12.1 README marks animation control incomplete, and an animation may contain
undocumented body or leg motion. The implementation uses the stock sound catalog
and individual head/LED APIs instead.

## Simulation

Run:

```text
python scripts/tasks.py encounter-sim
```

The scenario detects a simulated BB-8, performs three seeded reactions, records
every selected primitive, asserts no movement, and ends offline in safe hold.
The normal test suite covers absent droids, unsafe battery, failed/invalid chat,
privacy, reaction bounds, no immediate repetition, default denial, stock-enum
allowlisting, and restoration.

## Real-hardware gate

`scripts/hil_stationary_droid_encounter.py` is a separately invoked local HIL
command and is absent from hosted CI. Its default invocation refuses before BLE
scanning. A real run requires:

- the operator present with device inspection complete;
- temperature within the documented operating range;
- the one-meter keep-out zone clear and emergency-stop path ready;
- explicit charging-safe-only and second-go confirmations;
- `R2_DEVICE_IDENTITY` supplied outside source control;
- `R2_ENCOUNTER_ARM_TOKEN=AUTHORIZE_STATIONARY_HEAD_AUDIO` supplied externally;
- one to five reactions, with three as the default.

The command scans before connecting to R2, records only droid classes, checks R2
battery, performs the bounded reactions, restores expression state, attempts the
normal fail-closed stop/disconnect cleanup once, and writes immutable sanitized
evidence. Run it under an external process watchdog on the Pi because the pinned
library synchronously waits for command responses and the charging firmware has
previously timed out on the final motor-OFF acknowledgement.

The reviewed external wrapper is also separately disabled. For a newly
authorized run, the operator supplies
`R2_ENCOUNTER_WATCHDOG_TOKEN=AUTHORIZE_WATCHDOG_STATIONARY_ENCOUNTER` and invokes:

```text
python scripts/hil_watch_stationary_droid_encounter.py --authorize-watchdog-run --timeout-seconds 40
```

It refuses reused journal/evidence paths before starting the child. A normal
child exit is passed through without creating timeout evidence. On timeout it
terminates the child, escalates to a kill only if the five-second termination
grace also expires, validates the durable journal, and writes the immutable
sanitized watchdog report automatically. The report explicitly leaves BLE
disconnect unverified and requires operator state confirmation; process
termination is not proof of safe physical cleanup. Controller-level cleanup and
zero residual-connection verification remain operator steps.

This is expression-capability evidence, not permission to advance Gate P1 or a
claim that stock animations are safe.

### First live attempt

On 2026-08-11 the operator confirmed the physical preflight. The target wheel
hashes and Pi CPU temperature (40.407°C) passed. A 40-second external watchdog
expired after the session established an R2 BLE link but before it produced an
immutable report. Python was terminated and the residual link was removed by
powering off and soft-blocking the controller, with zero connections afterward.
No retry was made. Primitive completion remains indeterminate until the operator
reports what was directly seen and heard. The operator later confirmed that an
expression was seen or heard and that R2 ended stationary, silent, and with its
normal LED state. Because the confirmation did not distinguish head, LED, and
audio primitives individually and no report was produced, this remains a timed-
out characterized attempt rather than a passing HIL cycle.

After this attempt, the session gained an append-only progress journal. Each
stage is flushed and fsynced before the next vendor operation so an external
watchdog still leaves the last completed stage. Records contain only sequence,
stage, droid-class count, battery-safe boolean, and reaction number. Device
identity, BLE address, exception detail, semantic/audio selection, and packet
data are forbidden. This journal is simulation-tested but was not deployed for
the first live attempt.

### Watchdog evidence recovery

After a watchdog terminates the process, classify the journal before any retry:

```text
python scripts/classify_encounter_watchdog.py --progress <progress.jsonl> --output <evidence.json>
```

The offline recovery command validates the exact journal state-machine prefix, sequence,
stage-specific value types, reaction numbering, and terminal ordering. Invalid
or tampered input fails without producing a report. A valid or absent journal
produces immutable, deterministic timeout evidence containing only the last
durable stage, a stable stall classification, marker/reaction counts, and
explicit privacy/safety assertions. It does not copy droid kinds, identities,
addresses, exception text, chosen sounds, or chat meanings.

`completed` means the progress journal reached `session_completed`; it does not
convert an externally timed-out invocation into a passing HIL cycle. The
watchdog report remains terminal `watchdog_timeout`, and operator observation
and normal session evidence must still be evaluated separately.

Commit `8c5bae3` was copied into a new rollback-safe Pi staging directory at
`/home/pi/r2d2-hil-8c5bae3`. SHA-256 hashes for all five changed runtime/runner
files matched the committed workstation files. With Bluetooth soft-blocked, the
offline command classified an intentionally absent journal as `no_progress` and
wrote deterministic `watchdog_timeout` evidence with SHA-256
`fb53159fe9f63e69a37a9a3b0c28bc97ead6e1df25dc1c2f7ded1e8101193c86`.
No scan, droid connection, command, or actuation occurred.

Commit `7c90a1f` passed hosted simulation CI run `31564021923` and was copied to
new rollback-safe Pi staging `/home/pi/r2d2-hil-7c90a1f`. The three changed-file
SHA-256 hashes matched. With Bluetooth soft-blocked and no arm token or flag, the
wrapper exited 1 with its disabled message, created no progress/live/watchdog
file, and never started the child launcher. No droid was accessed.

### Authorized run with durable evidence

After the operator supplied a new stationary-only authorization and confirmed
the physical preflight, the first invocation of the new staging stopped before
scanner import because the isolated dependency path was missing. Bluetooth was
re-blocked, no scan or droid access occurred, and a tested launcher fix was
committed as `919713f`; hosted run `31564493652` passed.

The corrected run found one nearby droid class, connected to R2, verified a safe
battery state, and durably marked reaction 1 as started. The reaction did not
reach its completed marker: the child recorded a sanitized `EOFError`, reached
`disconnect_started`, and then the 40-second watchdog terminated the process.
The controller was powered off and soft-blocked afterward. This is a failed,
non-retry HIL attempt and not a Gate P1 cycle. Operator observation of the
physical expression and final droid state was still required when this evidence
was captured.

The operator subsequently reported that no sound, dome movement, or LED reaction
was observed; the base, legs, heading, and location did not change; and R2 ended
stationary, silent, with all LEDs off. This confirms the observed final physical
state and absence of locomotion, but it does not prove that individual software
restoration commands were acknowledged. The attempt remains a characterized
failed HIL run and does not count toward Gate P1.

Offline inspection of pinned `spherov2.py` 0.12.1 confirmed that every expression
primitive uses `_execute()` and waits up to ten seconds for a firmware response.
The pre-fix adapter could then mask the first primitive error with a later
restoration error and, after an EOF, attempt another response-waiting motor-OFF
command before closing BLE. The corrected adapter records only a stable phase
such as `head_position_read`, `logic_display_set`, or `audio_play`, preserves the
first exception type, attempts every restoration step, and treats EOF/connection
loss as a failed transport so disconnect closes the adapter without that futile
wait. It does not claim the droid received a stop or restoration command.

The existing attempt-3 journal predates this phase instrumentation, so its exact
failing expression primitive remains unknown. The fix is simulation-tested and
is not authorization for another hardware run.

Commit `c9f344e` passed hosted simulation CI run `31609883254` and was copied to
new rollback-safe Pi staging `/home/pi/r2d2-hil-c9f344e`. All five changed-file
hashes matched. The import-only default-refusal path loaded successfully and
exited before backend construction; Bluetooth remained soft-blocked and no
evidence file, scan, connection, or droid command occurred.
