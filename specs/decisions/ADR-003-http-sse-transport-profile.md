# ADR-003: HTTPS JSON plus SSE as the MVP transport

- Status: Accepted
- Date: 2026-08-11

## Context

The first integration runs on a home LAN with a Pi, PC/laptop, browsers, and microphone nodes. It needs simple debuggable commands, resumable events, artifact transfer, and future transport replaceability.

## Decision

Use HTTPS JSON for request/response, Server-Sent Events for ordered resumable event delivery, and bounded multipart HTTPS for artifacts. Define payloads independently of transport. Preserve event IDs, producer sequence, measurement time, monotonic time, clock uncertainty, and idempotency so MQTT/NATS/WebSocket/ROS adapters can be added later.

## Consequences

- Simple FastAPI/Apache/browser integration and packet inspection.
- SSE is one-way per server; each role hosts a stream and uses the peer API for requests.
- High-rate raw audio stays out of events and moves as content-addressed artifacts.

