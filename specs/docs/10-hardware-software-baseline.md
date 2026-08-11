# 10 - Hardware and software baseline

## 1. R2 Agent Runtime hardware

### 1.1 Required reference configuration

| Item | Reference | Notes |
|---|---|---|
| Droid | Sphero R2-D2 R201 | BLE 4.0, wired USB charging, 0-40 C manual envelope |
| Controller | Raspberry Pi 4B Rev 1.2, 4 GB | User's existing LAMP server; reference deployment |
| Power | Quality Pi 5 V / 3 A supply | Avoid undervoltage under USB audio/storage load |
| Storage | 32 GB minimum; 64 GB high-endurance or SSD recommended | Retention/recordings can dominate; monitor writes/free space |
| Network | Ethernet preferred, Wi-Fi supported | BSM/audio artifacts benefit from wired LAN |
| Bluetooth | Integrated adapter initially | Optional quality USB BLE adapter if coexistence/range testing requires it |
| Microphone | USB mic or supported array | Select stable ALSA device ID; benchmark wake/STT |
| R2 speech/probe speaker | R2 onboard sound for character; optional Pi USB speaker for custom audio/probes | Mapping requires a characterized source |
| Stop input | PWA plus local command; optional normally closed GPIO button | GPIO strongly recommended before broader autonomy |
| Ambient sensor | Optional temperature/humidity sensor | Needed for environmental monitoring/speed-of-sound refinement; not R2 CPU temp |

Keep chargers, cables, and the R2 physical unit inspectable and accessible. Do not enclose the battery/charger or modify it as part of MVP.

### 1.2 Reduced Pi 3 profile

A Raspberry Pi 3B+ can run BLE control, safety, basic web/API, wake word, and modest continuity if tested. Offload or disable local Whisper/LLM/heavy audio work. Resource budgets and gates are profile-specific; Pi 4 remains the reference.

### 1.3 Resource budgets on Pi 4

Initial budgets to verify, not hard guarantees:

| Resource | Core reserve/target |
|---|---|
| CPU | Preserve one core-equivalent capacity for BLE/safety/OS under peak optional load |
| RAM | Core BLE/safety/API/DB target <768 MB; all R2 services target <2.5 GB without model cache |
| Disk | Alert at 20% free; stop nonessential recording before critical low space |
| Temperature | Monitor throttling and CPU temperature; degrade optional inference before control |
| Event backlog | Bounded queues with disk spill/audit and visible degraded state |

Measure on the actual Pi. Optional workers have limits and lower scheduling priority than safety/BLE.

## 2. BSM hardware

### 2.1 Development/simulation host

| Resource | Minimum | Recommended first serious experiments |
|---|---:|---:|
| CPU | 4 modern cores | 8+ cores |
| RAM | 8 GB | 16-32 GB |
| Storage | 20 GB free | 100+ GB SSD for recordings/artifacts |
| GPU | None | Optional supported GPU for selected solvers; CPU baseline remains |
| OS | Current supported 64-bit Linux/macOS/Windows | Linux for server, macOS viable on MacBook Air |

### 2.2 Acoustic reference array

- Shared-clock USB/multichannel interface
- Four input channels minimum for initial experimental 3D localization geometry; six to eight preferred for robustness/reflections
- Matched or individually calibrated microphones, stable stands, measured acoustic centers
- Known cable/channel mapping
- 48 kHz/24-bit minimum preferred; 96 kHz when the whole chain supports it and experiments justify storage/compute
- Calibrated speaker/probe source mounted with measured transform to the agent
- Sound-level meter or calibrated measurement method for probe safety
- Temperature/humidity measurement
- Independent tape/laser/reference measurements for real-room ground truth

Consumer phones/tablets/laptops are valuable auxiliary nodes and first experiments, but their unknown clocks, processing, AGC, and buffering must be measured. They are not equivalent to a shared-clock array.

## 3. R2 software baseline

| Layer | Reference choice | Boundary/notes |
|---|---|---|
| OS | Existing compatible 64-bit Raspberry Pi OS/Debian-based Linux | Audit before upgrade; BlueZ/ALSA/systemd required |
| Backend | Python 3.11 | Pin in toolchain; verify native wheels on ARM64 |
| Package management | `uv` with lockfile, or equivalent reproducible Python tooling | Do not install app deps into system Python |
| BLE | Reviewed/pinned `spherov2.py` 0.12.1-derived adapter plus explicit `bleak` dependency | Unofficial/reverse-engineered; vendor/fork if fixes needed |
| API/models | FastAPI, Pydantic v2, Uvicorn | Public SAP models generated/validated separately |
| Persistence | SQLAlchemy 2, Alembic, SQLite WAL | Secrets excluded; future store adapter possible |
| Wake | openWakeWord adapter initially | Benchmark custom "Hey R2" on actual mic/room |
| VAD/STT | replaceable VAD plus `whisper.cpp` tiny/base benchmark | Do not assume real time; LAN/remote adapter supported |
| Reasoning | `smolagents` `ToolCallingAgent` adapter | Python >=3.10; API considered replaceable/experimental |
| Web | TypeScript PWA, pinned active-LTS Node toolchain | Minimal dependencies; Safari/iPhone foreground behavior tested |
| Service | `systemd`; Apache TLS/reverse proxy | Host-native BLE/audio |
| Observability | structured JSON logs, Prometheus/OpenTelemetry adapters | Sensitive payloads off by default |

Exact versions beyond the supplied `spherov2.py` baseline are selected and locked during Phase 0 after compatibility tests. Specs name interfaces, not floating package versions.

## 4. BSM software baseline

| Layer | Reference choice | Boundary/notes |
|---|---|---|
| Runtime/API | Python 3.11, FastAPI/Pydantic | Same language eases protocol generation; independent package |
| Numerical | NumPy, SciPy | Core reference algorithms and fixtures |
| Audio | SoundFile/libsndfile plus native capture adapter | Preserve original samples/metadata; audio host-specific |
| Acoustic simulation | project analytic fixtures; optional Pyroomacoustics adapter | Ground truth isolated from estimator |
| Geometry | project models; optional Open3D adapter | Export PLY/GLB/GeoJSON |
| Acceleration | optional JAX/PyTorch/GPU adapter | No GPU requirement for conformance/CPU smoke suite |
| Metadata | SQLite initially; SQLAlchemy/Alembic | PostgreSQL/PostGIS later adapter |
| Artifacts | content-addressed filesystem initially | Object-store adapter later |
| Jobs | local process pool initially | Queue/distributed worker adapter later |
| UI | TypeScript web UI or notebooks for algorithm diagnostics | Production operator controls remain web/API |
| Deployment | native dev; containerized core supported | Capture nodes native |

## 5. Protocol/tooling baseline

- OpenAPI 3.1 for request/response endpoints
- JSON Schema 2020-12 for shared payloads/events
- SSE for MVP event transport with cursor/resume
- RFC 3339 UTC plus producer monotonic nanoseconds and clock uncertainty
- SI units, right-handed frames, quaternions, covariance
- SHA-256 artifact integrity
- Generated Python/TypeScript boundary clients, but domain code maps generated types into owned internal models

## 6. Developer quality tools

- Ruff format/lint
- mypy or Pyright strict-enough type checks
- pytest, pytest-asyncio, Hypothesis, coverage
- OpenAPI/JSON Schema linter/validator
- Playwright plus accessibility checks for PWA
- pre-commit hooks that mirror CI but do not hide modifications
- dependency/SBOM/license/secret scanners
- Makefile/task runner with stable commands

Choose one tool per job during scaffold and document it; do not add overlapping frameworks casually.

## 7. Version policy

- Pin all production and development dependencies.
- Use automated update proposals, never unattended deployment.
- Review changelogs and run full sim/contract tests before merge.
- BLE/audio/crypto/ORM framework changes require targeted HIL/migration/security tests.
- Model files and probe waveforms are versioned by hash.
- Firmware capability profiles are bound to observed firmware/system identifiers, not assumed universal.

## 8. Hardware identification and privacy

MAC addresses, serial numbers, Wi-Fi credentials, and room-specific coordinates stay in device/site configuration or secrets. Examples use synthetic identifiers. Capability reports can retain a one-way local device reference where necessary without publishing the address.

