# ADR-001: Independent products joined by SAP

- Status: Accepted
- Date: 2026-08-11

## Context

R2 Agent Runtime must reach MVP first, while Bat-Space Modeler later becomes a reusable system for other agents. Direct calls to R2-specific classes or a shared database would make both products difficult to replace or deploy separately.

## Decision

R2 Runtime and BSM are independent deployables with independent persistence. Their first required integration uses the same versioned Spatial Agent Protocol exposed to every later agent/provider. Shared runtime code is limited to the protocol package, schemas, generated boundary clients, and conformance fixtures.

R2 exposes a generic Mobile Agent surface and consumes a generic Spatial Provider surface. BSM consumes a generic Mobile Agent surface and exposes a generic Spatial Provider surface.

## Consequences

- More explicit schemas/adapters and contract tests are needed early.
- R2 MVP work must include fake/provider adapter paths before BSM algorithms exist.
- BSM can develop against SimMobileAgent and integrate R2 without solver rewrites.
- Separate deployment and data lifecycle are preserved.

