# Focused phase task prompt

Use this after the workspace exists. Replace bracketed fields.

---

Continue the R2 Runtime + Bat-Space Modeler workspace under the repository `AGENTS.md` and normative specs.

Target milestone: `[for example: Phase 1 - R2 hardware capability probe]`  
Requirements: `[IDs from specs/traceability/requirements.csv]`  
Primary acceptance scenarios: `[scenario IDs from specs/docs/07-simulation-and-test-plan.md]`  
Requested scope: `[specific vertical slice]`  
Hardware authorization: `[none / stationary only / exact bounded motion test described here]`

Read the relevant specifications, ADRs, schemas, `STATUS.md`, and current implementation first. Then implement and verify the smallest end-to-end slice that materially advances the target acceptance gate. Do not stop after planning.

Preserve these invariants:

- independent R2 and BSM builds/data/deployments;
- SAP-only cross-system integration;
- simulator/default no-real-motion behavior;
- deterministic local R2 safety/leases/stop;
- no LLM or BSM motor authority;
- explicit time/frame/units/uncertainty/provenance;
- graceful degradation and auditable command lifecycle.

Add/update tests, fixtures, schemas, docs, traceability, and `STATUS.md` in the same change. Run the applicable formatting, lint, type, unit, contract, simulation, migration, browser, and package checks. Do not claim HIL or real-room evidence unless it was explicitly authorized and actually measured.

Return the completed outcome, evidence, remaining gate items, limitations/safety implications, and exact next task.

---

