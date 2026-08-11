# Release/gate verification prompt

---

Audit the current workspace against `[gate name, e.g. R2 MVP gate]` in `specs/docs/09-roadmap-and-acceptance.md`.

Read `AGENTS.md`, all specs/ADRs relevant to the gate, traceability, changelogs, `STATUS.md`, current code, test configuration, deployment artifacts, and existing evidence. Treat this as an evidence audit plus permission to fix repository-local defects required by the gate. It is not permission to move real hardware, access credentials, push/deploy externally, or weaken a requirement.

For every gate item:

1. map it to requirement IDs, implementation, and independently meaningful evidence;
2. run or reproduce the applicable deterministic checks;
3. distinguish unit/contract/simulation/HIL/real-room/operator evidence;
4. detect skipped tests, false-green mocks, shared-code boundary violations, stale schemas/docs, unsafe defaults, missing failure coverage, and unverified numerical claims;
5. fix in-scope code/tests/docs where safe and rerun checks;
6. leave any evidence requiring real hardware/room/credentials explicitly incomplete unless separately authorized.

Also prove:

- R2 and BSM each build/test with the peer source absent;
- SAP version/capability/idempotency/time/frame/uncertainty conformance;
- stop/safe-hold final states under failure and restart;
- simulation is the default and hosted CI cannot address motors;
- dependency locks, migrations, install/upgrade/rollback/backup instructions, security/privacy controls, and SBOM/license status;
- all published performance/accuracy statements name their evidence category and operating envelope.

Update `STATUS.md` and traceability with exact commands, artifacts, dates, and pass/fail/incomplete state. Do not mark the gate passed when any mandatory evidence is missing.

Return a concise gate decision (`PASS`, `FAIL`, or `INCOMPLETE`), fixed items, checks/evidence, remaining blockers ranked by risk, and the smallest next action.

---

