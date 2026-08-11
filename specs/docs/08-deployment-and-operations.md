# 08 - Deployment and operations

## 1. Environment profiles

| Profile | Purpose | Real motion | External services |
|---|---|---:|---|
| `dev-sim` | Local development with all simulators | Never | Optional/mocked |
| `ci` | Deterministic automated verification | Never | None |
| `pi-stationary` | Real BLE/audio capability and stationary expression tests | Disabled | Optional |
| `pi-motion-lab` | Explicit supervised bounded R2 movement | Armed per run | Optional |
| `bsm-sim` | Acoustic/agent simulation | Never | None |
| `bsm-bench` | Fixed source/microphone calibration experiments | Agent optional/stationary | None required |
| `integration-lab` | Supervised R2 + BSM | Armed per mission | Local LAN |
| `production-home` | Approved features in known space | Policy-controlled/supervised | Configured |

Configuration profiles cannot enable motion merely because an environment variable is present; hardware arming is an explicit runtime action with expiry.

## 2. Source workspace

Recommended layout:

```text
sphero-droids/
  AGENTS.md
  STATUS.md
  Makefile
  specs/
  protocol/
  r2-runtime/
  bat-space-modeler/
  integration-lab/
  deploy/
```

Each product has its own package manifest, lockfile, migrations, tests, container/service definitions, version, changelog, and README. Root automation orchestrates but does not create runtime imports.

Required developer commands after scaffold:

```text
make bootstrap        install pinned development dependencies
make check            format-check, lint, type-check, unit/component tests
make contract         validate schemas and run SAP conformance
make sim-smoke        deterministic R2/provider/acoustic smoke scenarios
make test             check + contract + sim-smoke
make package          build standalone artifacts without deployment
make docs-check       links, schemas, examples, traceability
```

Hardware commands are separate, explicit, and never dependencies of `make test`.

## 3. Raspberry Pi deployment

### 3.1 Pre-install audit

The user's Pi already runs LAMP. Before changing it, collect and save:

- Raspberry Pi model/RAM/architecture and OS release;
- Python, Apache, PHP, database, Bluetooth/BlueZ, and audio stack versions;
- enabled services, listening ports, storage/free space, and boot configuration;
- current `/var/www`/Apache configuration relevant to the new virtual host;
- Bluetooth/audio device enumeration;
- tested backup/restore path.

Do not perform an in-place OS upgrade as part of the application install. Report incompatibilities and stage migration separately.

### 3.2 Filesystem layout

Reference paths may be configured, but the package should default conceptually to:

```text
/opt/r2-runtime/releases/<version>/   immutable application release
/opt/r2-runtime/current -> ...        atomic active symlink
/etc/r2-runtime/                      non-secret configuration
/var/lib/r2-runtime/                  DB, artifacts, capability/calibration state
/var/log/r2-runtime/                  only if not using journald exclusively
/run/r2-runtime/                      Unix sockets and runtime state
```

Secrets use system credentials or root-readable environment/credential files, not `/var/www`, Git, database payloads, or browser-delivered configuration.

### 3.3 Service identities

- Dedicated unprivileged `r2` service account
- Minimum Bluetooth/audio/GPIO group/capabilities required
- No interactive shell or broad sudo
- Separate permissions for core, BLE, audio, worker, and web where practical
- Writable access limited to `/var/lib/r2-runtime` and `/run/r2-runtime`

### 3.4 `systemd`

Units declare ordering and failure behavior:

- `r2-ble.service`
- `r2-core.service`
- `r2-audio.service`
- `r2-worker.service`
- optional `r2-backup.timer`, retention and health timers

Use restart backoff and start limits. A unit restart must not restore movement. Shutdown invokes safe hold with a bounded timeout; OS shutdown cannot hang indefinitely on BLE.

### 3.5 Apache/PWA

Apache terminates HTTPS and reverse-proxies a dedicated path/virtual host to loopback R2 API/PWA. Required controls:

- TLS and secure headers;
- authentication/session protection;
- Web/SSE proxy settings with bounded timeouts;
- request size/rate limits;
- no direct exposure of Unix sockets, DB, artifacts, debug endpoints, or secrets;
- distinct operator and read-only access where implemented.

The PWA service worker cannot cache authenticated API responses or stale emergency state. It may cache versioned static assets and offline operator guidance.

## 4. BSM deployment

### 4.1 Core

BSM can run:

- natively in a Python virtual environment for development/audio access;
- as containers for API, workers, metadata DB, and artifact services;
- as a packaged desktop/server service later.

The first target should be Linux or the user's MacBook Air for development. Windows is supported by keeping filesystem/audio/device adapters explicit; WSL is not assumed to provide low-latency microphone access.

### 4.2 Data layout

```text
bsm-data/
  metadata/        SQLite/PostgreSQL config
  artifacts/       content-addressed recordings/features/maps
  cache/           rebuildable temporary data
  exports/         user-requested portable bundles
  calibration/     immutable calibration manifests/artifact links
```

Raw evidence and cache have separate retention. A cache purge cannot delete canonical evidence.

### 4.3 Microphone nodes

Each node runs a minimal native capture agent that:

- enrolls with explicit operator approval;
- reports devices/capabilities/processing state;
- performs calibration/clock checks;
- captures only armed windows;
- writes locally before upload to survive network loss;
- hashes and uploads bounded artifacts;
- exposes a visible capture/privacy state;
- deletes local staging only after a verified receipt and retention policy.

Old phones/tablets may need platform-native apps for reliable foreground capture. A browser PWA is an optional coarse node, not a guaranteed precision/background recorder.

## 5. Networking

- Give Pi, BSM, and fixed nodes stable DHCP reservations or service discovery names; do not bake IPs into code.
- Prefer wired Ethernet for BSM and fixed audio nodes where possible.
- Use a dedicated trusted LAN/VLAN if available.
- Deny public internet ingress; remote access uses an authenticated VPN/reverse tunnel explicitly configured by the operator.
- BLE remains local to the Pi; BSM never connects directly to R2.
- Firewall exposes only Apache/R2 and BSM/node ports required by the selected profile.

## 6. Secrets and credentials

Secrets include TLS private keys, API/session keys, model-provider keys, email OAuth tokens, notification tokens, and backup credentials. Requirements:

- `.env.example` contains names only;
- secret files are excluded from Git and backups unless encrypted;
- logs/config dumps redact values;
- rotation does not require code changes;
- R2 continues deterministic local operation if optional credentials are absent;
- development, HIL, and home-production credentials are separate.

## 7. Release artifacts

Every release records:

- product and SAP versions;
- Git commit and dirty-state policy;
- dependency lock/SBOM and licenses;
- supported OS/architecture/profile;
- DB migration range;
- configuration schema version;
- simulator/conformance results;
- HIL/real-room evidence if claimed;
- artifact hashes/signatures;
- upgrade and rollback notes.

Pi release activation is atomic. Keep at least one known-good release and a compatible database backup. Rollback never restores active movement/missions.

## 8. Database migrations

- Back up before migration and verify the backup can be opened.
- Migrations are automated, versioned, and tested from every supported release.
- Long/destructive migrations require explicit maintenance mode.
- Services remain safe-held during R2 migrations.
- A failed migration leaves the prior release/data recoverable and reports the exact state.

## 9. Health and observability

### R2 health

- BLE state/reconnect count/last command latency
- safety state, active lease, stop/watchdog counters
- telemetry freshness and battery state
- audio device/overruns/wake metrics/STT latency
- CPU temperature/load/throttling, memory, disk, network
- event backlog/DB/artifact/backup state
- provider connection/map/advisory freshness

### BSM health

- node enrollment/readiness and clock uncertainty
- capture completeness/clipping/dropouts
- ingest/job queues and failures
- algorithm runtime/memory and abstention/error metrics
- map revision/validation state
- artifact capacity/retention/backup
- agent sessions and mission state

Metrics avoid transcript/email/audio payloads. Logs use correlation IDs and bounded rotation.

## 10. Backup

### R2

- consistent continuity DB snapshot;
- configuration excluding or separately encrypting secrets;
- capability/calibration profile;
- selected artifacts/tags/routes;
- release/manifest information.

### BSM

- metadata DB;
- calibration and map manifests;
- selected raw evidence according to retention;
- artifact hashes and configuration/algorithm versions.

Backup success is not assumed from exit code alone: periodically restore into an isolated environment and run integrity/replay checks.

## 11. Upgrade/rollback sequence

1. Announce maintenance and safe-hold R2.
2. Verify no active mission/capture and persist event cursors.
3. Confirm current health, free space, backup, and rollback artifact.
4. Stage and verify release hashes/signatures.
5. Apply compatible migrations/config changes.
6. Start services in dependency order; run stationary smoke tests.
7. Require operator re-arming before physical movement.
8. If failure, stop services, restore compatible release/data, and remain safe-held.

## 12. Deployment acceptance

- Fresh install from documented prerequisites succeeds.
- Reinstall/upgrade is idempotent and preserves user data/config.
- Uninstall can preserve data by default and states exactly what is removed.
- Reboot starts healthy services with R2 stopped.
- Loss/recovery tests for BLE, BSM, microphone, network, DB, disk pressure, and optional model pass.
- Backup/restore and prior-release rollback are demonstrated before home-production designation.

