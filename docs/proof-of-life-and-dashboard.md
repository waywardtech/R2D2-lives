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
`status.json`, emergency state, chat requests, or authenticated API data. The
deployment is non-actuating and restricted by Apache to loopback/private-LAN
addresses. It does
not yet satisfy the full authenticated P2 operator-control requirement in
R2-012: emergency stop, deadman manual controls, authentication, and a live
reasoning service remain future gates. The dialogue fallback runs locally in the
browser and cannot issue physical commands.

The dashboard prefers a loopback FastAPI conversation service through Apache at
`/R2D2/api/chat`. It retains at most 40 recent turn pairs per opaque browser
session in an Alembic-migrated SQLAlchemy/SQLite database and remembers an
explicitly supplied preferred name. Strict Pydantic request models reject
unknown fields and messages outside 1-280 printable characters. The service has
no hardware driver, BLE dependency, command tool, arbitrary URL, or shell
surface; movement language receives a conversational refusal. If the service is
unavailable, the browser visibly activates its earlier local reply table.
The target's separately installed Python 3.11 lacks Debian `ensurepip` support,
so deployment creates an isolated `venv --without-pip` and installs the exact
hash-locked aarch64 wheels into that environment's site-packages with the system
installer's `--target` mode; system Python packages remain untouched.

The initial personality profile is grounded in Lucasfilm's official R2-D2
Databank description: reliable, versatile, brave, helpful, and enduringly loyal,
with the familiar prickly friendship with C-3PO. StarWars.com's official sound
design history describes R2's voice as whistles and beeps carrying thought and
emotion, while an official *Clone Wars* rewatch characterizes Artoo as mouthy.
The UI therefore presents an electronic vocalization first and a readable Basic
display translation, never audible English dialogue. The local persona is
resourceful, courageous, loyal, dryly irreverent, and occasionally stubborn; it
must not fabricate canon events or claim memories absent from bounded continuity.
Sources: [`R2-D2 Databank`](https://www.starwars.com/databank/r2-d2),
[`Iconic Star Wars Sound Effects`](https://www.starwars.com/news/5-iconic-star-wars-sound-effects-and-how-they-were-made-starwars-com), and
[`The Clone Wars Rewatch: Secret Weapons`](https://www.starwars.com/news/the-clone-wars-rewatch-secret-weapons).

An optional provider-neutral, OpenAI-compatible text adapter can extend the
conversation while preserving the same non-actuating boundary. It receives at
most eight recent turn pairs and a bounded sanitized status snapshot, has no
tools, and may return only an electronic vocalization plus a Basic display
translation. Invalid output, transport failure, or timeout falls back to the
deterministic local personality. The configured endpoint must use HTTPS (or
loopback HTTP for a local model), and redirects are rejected. Endpoint, model,
and credential-file settings are all-or-none so configuration mistakes fail
visibly at startup. The API credential remains outside source control; a
systemd credential can expose its runtime path through
`R2_CHAT_API_KEY_FILE`, alongside `R2_CHAT_MODEL_ENDPOINT` and
`R2_CHAT_MODEL` in a local service drop-in. No model provider or credential is
configured on the Pi in the current release, so live chat continues in local
mode.

The deterministic local mode supports preferred-name and recent-topic recall,
identity and capability questions, mood, greetings, thanks, farewells, battery,
system health, and bounded issue summaries. Ambiguous yes/no replies request one
more detail instead of fabricating context. Movement language remains an
explicit refusal, and word-boundary matching prevents unrelated words from
being mistaken for commands.

The first live conversational rollout is Pi release `9e7cfda`. The sandboxed
`r2-chat` service passed loopback health and public HTTPS chat checks, rejected a
movement request conversationally, reported `physical_action: false`, applied
Alembic revision `0001_chat_continuity`, and recalled the explicitly supplied
name `Luke` on the second turn of one opaque session. Apache and the dashboard
remained healthy; Bluetooth was inactive and soft-blocked for the entire rollout.

Pi release `e0c54fe` adds the optional model adapter but deliberately leaves it
unconfigured. Live loopback health and public HTTPS chat remained in `local`
mode and reported `physical_action: false`; the dashboard returned HTTP 200.
Bluetooth remained inactive and soft-blocked, and the service environment
contained no model endpoint, model name, or credential-file setting.

Console text uses the freely licensed Clynese Hand face from the AurekFonts
Archive. R2's English translation remains in a conventional condensed Latin
face for immediate readability. The bundled font is attributed to AurekFonts;
the archive classifies it as free for everyone, forever.

English translation lines are displayed directly, without a `Translation:`
prefix or enclosing quotation marks, so the available console space is devoted
to the translated dialogue. R2 translations use a heavy futuristic Latin font
stack at twice the base dialogue size and begin with a same-size right-pointing
triangle; long lines remain responsive and wrap within the transcript.

The console occupies the available browser viewport without page scrolling;
individual transcript and telemetry bays scroll only when their content needs
it. Its live scopes visualize status-derived mood, optional foreground
microphone input, and R2 dialogue-output activity. Microphone capture starts
only after the operator presses `ENABLE`, stops on a second press or page exit,
and is never uploaded or persisted. The header's red micro-LED matrix changes
with local module calls such as status refresh, chat input, translation, and
microphone state. These visual signals do not expose a physical-control path.

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
The reviewed proof-of-life watchdog is separately armed, accepts only a 20-120
second bound, refuses existing evidence paths before child creation, terminates
then kills a hung child if necessary, and emits immutable identity-free timeout
evidence classified from the last durable phase. A timeout always requires
operator confirmation and never causes an automatic retry.

Live launchers require `R2_DEVICE_IDENTITY` to be supplied outside source
control before scanning. Discovery may observe other R2-class advertisements,
but proceeds only when exactly one advertisement matches the configured identity.
Zero or duplicate exact matches fail closed without logging any advertised name
or BLE address. A launcher never adopts the first or only nearby display name as
identity.

The proof-of-life session preserves a sanitized stable failure phase across
connect, identity, battery, head query, expression subphase, ready transition,
and disconnect. If disconnect also fails, its exception type is recorded as
cleanup uncertainty without replacing the primary failure. Exception messages,
identities, and transport payloads are never written to the report.

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
