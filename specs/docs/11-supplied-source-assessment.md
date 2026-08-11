# 11 - Supplied-source assessment

Assessment date: 2026-08-11

## 1. Selection rule

The implementation uses the smallest source set that directly supports R2-D2 R201 BLE behavior. Older, device-specific, deprecated, or RVR-only packages are retained as historical/reference evidence and are not copied into production blindly.

## 2. Source inventory

| # | Supplied file | Assessment | Use |
|---:|---|---|---|
| 01 | `R2-D2 Manual.pdf` | R201 safety/regulatory manual | Normative physical safety/temperature/charging/visibility source |
| 02 | `R2-D2 User-Manual-3480092.pdf` | Near-duplicate R201 manual revision | Cross-check manual text; no separate software API |
| 03 | `BB-8 Manual.pdf` | BB-8 safety/regulatory manual | Future BB-8 adapter safety only; not R2 implementation |
| 04 | `BB-8 User Instructions.pdf` | BB-8 operation instructions | Future reference; no R2 dependency |
| 05 | `sphero.js-master.zip` | Explicitly deprecated official JavaScript SDK for robots through mid-2016; includes BB-8 examples | Protocol/history reference only; not production |
| 06 | `sphero-sdk-raspberrypi-clientjs-master.zip` | Sphero RVR Client.js SDK | RVR architecture/reference only; not R2 BLE |
| 07 | `PythonSphero-master.zip` | Tutorials using Kulka for Sphero 1/2 | Educational/legacy reference only |
| 08 | `sphero-sdk-raspberrypi-nodejs-master.zip` | Sphero RVR Node.js SDK | RVR web/async reference only; not R2 BLE |
| 09 | `spherov2.py-main.zip` | Unofficial Python BLE v2 library; explicitly implements R2-D2/R2-Q5 | Selected R2 driver baseline, pinned/reviewed behind adapter |
| 10 | `sphero-sdk-raspberrypi-python-master.zip` | Sphero RVR serial/REST SDK | Async/design reference only; not R2 BLE |
| 11 | `Sphero-Mac-SDK-master.zip` | Deprecated/archived Objective-C Sphero SDK | Legacy sensor/API ideas only |
| 12 | `Sphero-iOS-SDK-master.zip` | Deprecated/archived iOS SDK | Legacy reference only; not modern iPhone node basis |
| 13 | `Sphero-AR-SDK-master.zip` | Deprecated Unity/iOS AR SDK for round Sphero tracking | Historical sensor-fusion/reference only; not R2 or BSM dependency |
| 14 | `Sphero Public SDK - Python SDK Setup (Advanced).pdf` | 2025 RVR Raspberry Pi setup guide; assumes Python 3.7 and RVR SDK | Pi/SDK setup context only; not R2 driver authority |
| 15 | `sphero-r2d2-rest-interface-main.zip` | Small Flask/`pygatt`/`gatttool` R2 packet demo with reconnect-per-command and hardcoded address | Packet/behavior reference; do not deploy or copy architecture |
| 16 | `app_enabled_droid_bb8.pdf` | BB-8 manual copy | Future BB-8 reference only |

## 3. Selected R2 baseline details

The supplied `spherov2.py` archive declares version 0.12.1, MIT licensing, Python >=3.7, and R2-D2 support. Inspection of the R2/BB-9E inheritance and commands shows:

- R2 device type/name filtering (`D2-`);
- BLE v2 handshake through the BB-9E base;
- drive with heading/raw drive and stabilization controls;
- locator, velocity, speed, attitude, quaternion, acceleration, gyro, and core-time stream definitions;
- collision and activity notifications;
- battery voltage/state and sleep/wake APIs;
- head angle/position, leg position/action, and stance-related animatronic APIs;
- eight R2 LED channels;
- 388 enumerated onboard audio IDs, including shared/other-droid families that must not be assumed appropriate for R2;
- 51 enumerated R2 animations;
- a `BleakAdapter` and optional TCP BLE relay.

Important engineering caveats:

- It is unofficial and based partly on reverse engineering.
- Its README says to install `bleak`, but `setup.py` does not list `bleak` in `install_requires`; the R2 project must declare it explicitly.
- Some controls are marked incomplete in the upstream README.
- Advertised methods may vary by R2 firmware and must be capability-probed.
- The library uses blocking/threaded wrappers around asyncio; it belongs behind a process/adapter boundary.
- Do not expose its low-level types as SAP or internal domain models.

The implementation should begin with a pinned source/commit or vendored fork carrying only reviewed compatibility fixes, with upstream license/attribution preserved.

## 4. Why the REST demo is not production architecture

The supplied Flask demo:

- hardcodes a BLE MAC address;
- uses deprecated `pygatt.GATTToolBackend`/`gatttool` style tooling;
- connects, handshakes, performs a command, sleeps, and disconnects per request;
- sleeps synchronously for six seconds in a web request;
- exposes unauthenticated debug-style endpoints;
- has no telemetry stream, safety lease, concurrency control, or persistent state.

Its packet sequences and command names are useful corroborating evidence only. Production uses one persistent BLE owner, typed high-level commands, authentication, deterministic safety, and a simulator.

## 5. Manual-derived constraints

The R2 manual states or supports:

- R201 identity and proprietary firmware/software relationship;
- operation/storage from 0 to 40 C (32 to 104 F);
- keep R2 visible during operation;
- keep approximately one meter between the operating droid and people/animals/property;
- avoid dangerous/hazardous/public areas;
- inspect for damage and do not self-service the battery/device;
- use the supplied USB cable and appropriate 5 V power source;
- do not charge damaged/leaking/hot devices, near flammable materials, covered, or outside the temperature range;
- wired USB charging, with no documented autonomous docking mechanism.

These restrictions are reflected in safety rules and operator gates. The manual does not document an application-accessible ambient-temperature sensor, so none is assumed.

## 6. License/provenance policy

- Preserve license and copyright notices for any reused code.
- Record the exact source archive/commit and local changes.
- Prefer clean adapter code using documented public call surfaces rather than copying demo application code.
- Do not mix source under unclear/incompatible licenses into the production package.
- Keep proprietary Star Wars/Sphero media on the user's owned device; do not redistribute extracted audio/firmware assets.
- Project documentation should state that the project is unofficial and unaffiliated with Sphero/Disney/Lucasfilm.

## 7. Verification backlog

The Phase 1 hardware probe must establish on the user's R201:

- BLE identity/handshake/reconnect behavior;
- firmware/system identifiers;
- battery state/voltage semantics and notification behavior;
- sensor stream names, units, axes, rate, and drift;
- collision thresholds and payload;
- safe head/leg/stance behavior;
- LED channel mapping and brightness;
- verified audio/animation subset, volume, duration, and interaction with motion;
- stop latency, command safe interval, and movement calibration;
- sleep/wake behavior and whether any command paths are firmware-sensitive.

Until verified, the capability status is `unverified`, not `supported`.
