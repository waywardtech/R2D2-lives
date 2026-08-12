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

The offline command validates the exact journal state-machine prefix, sequence,
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
