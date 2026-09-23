# R2 Runtime + Bat-Space Modeler workspace

> **Work in progress.** An active build of a safe control runtime for a Sphero
> R2-D2 (R201) droid, alongside the spatial-modeling work beside it. It is
> published so the work is visible, not because any part of it is finished.
> `STATUS.md` carries the current phase and gate state; interfaces change
> without notice, and real hardware movement stays behind the explicit
> authorization and safety gates described in `AGENTS.md`.

This incubation workspace contains two independently deployable products joined
only through the versioned Spatial Agent Protocol (SAP):

- `r2-runtime`: safe R2 control/runtime with simulation-default adapters and a
  separately gated, disabled-by-default R201 hardware profile;
- `bat-space-modeler`: generic spatial-modeler scaffold, with no acoustic solver
  development before the R2 MVP gate;
- `protocol`: public schemas, generated boundary types, and conformance tests;
- `integration-lab`: deterministic simulators and cross-contract scenarios;
- `specs`: the normative engineering specification pack.

Start with `AGENTS.md`, `specs/README.md`, and `STATUS.md`. On Windows, run:

```powershell
python scripts/tasks.py bootstrap
python scripts/tasks.py check
python scripts/tasks.py contract
python scripts/tasks.py sim-smoke
python scripts/tasks.py test
python scripts/tasks.py docs-check
python scripts/verify_ci_safety.py
python scripts/verify_repository_hygiene.py
```

GNU Make users can run the corresponding `make` targets. General automated paths
and hosted CI are simulation-only. Real BLE entry points are separate, refuse by
default, require exact local preflight/authorization, and are never invoked by
`test` or CI. Hardware access and any movement remain separately authorized.
