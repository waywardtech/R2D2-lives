# ADR-002: Contract-enforced incubation workspace

- Status: Accepted
- Date: 2026-08-11

## Context

A single developer/coding agent benefits from atomic protocol and integration changes, but standalone products need repository-grade boundaries.

## Decision

Begin in one workspace/repository with top-level `protocol`, `r2-runtime`, `bat-space-modeler`, and `integration-lab` projects. Each has its own manifest, lock, tests, migrations, version, build, and deployment. CI runs each with peer source absent and rejects cross-imports outside generated protocol packages.

The projects may be split into separate repositories after SAP 1.0 or independent release cadence demands it, without changing runtime code.

## Consequences

- Easier coordinated MVP development and one Codex context.
- Boundary enforcement is mandatory; directory proximity does not grant code sharing.
- Git history can later be filtered/split cleanly if project paths remain stable.

