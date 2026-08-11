# ADR-004: Host-native Pi services for BLE and audio

- Status: Accepted
- Date: 2026-08-11

## Context

The user's Pi 4 already operates as a LAMP server. BLE, ALSA/audio, GPIO, shutdown, and `systemd` watchdog access become more complex and fragile when containers are mandatory.

## Decision

Deploy R2 BLE/core/audio workers as host-native Python virtual-environment services supervised by `systemd`, with Apache as the existing HTTPS reverse proxy. Containers are allowed for development/simulation and BSM, but not required for R2 hardware access.

## Consequences

- Straightforward device permissions, service ordering, watchdog, and shutdown.
- Installation must carefully audit/preserve the existing LAMP host and system Python.
- Release directories, dedicated users, pinned virtual environments, atomic activation, and rollback are required.

