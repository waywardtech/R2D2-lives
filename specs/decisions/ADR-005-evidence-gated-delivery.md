# ADR-005: Evidence-gated delivery for R2 hardware work

- Status: Accepted
- Date: 2026-08-18

## Context

The R201 has accepted and visibly completed wake/stance commands, while several
bounded wheel-command variants have produced no observed locomotion. Adding
another command path without a distinct, observable hypothesis would consume
operator time and hardware-test risk without increasing knowledge.

The project needs one shared rule for research, implementation, test, and Pi
deployment work: a change advances only when it has a measurable benefit over a
recorded baseline. This is especially important for hardware diagnostics, where
packet transmission alone is not evidence that a droid accepted or executed a
command.

## Decision

Maintain an immutable-in-Git benefit register at
`planning/benefit-register.json`, checked by
`scripts/verify_delivery_benefit.py` in local and hosted verification.

Every proposed implementation, test, or deployment that changes public runtime
behavior or can access hardware MUST record:

- a unique decision ID and scope;
- a baseline with evidence references;
- one measurable outcome, unit, threshold, and collection method;
- the decision rule that defines benefit or no benefit;
- source references and whether each is official, upstream, or community;
- an explicit next action for either result.

Hardware-facing entries also require an operator-observable metric. A software
completion, queue write, or BLE connection cannot satisfy that metric alone.

Research entries may be added without a build. A proposed build or HIL action is
blocked by process when its hypothesis merely repeats a completed no-benefit
entry or has no stated measurement.

## Consequences

- The next R201 locomotion action is a source/packet-parity investigation, not
  another speed or duration variation.
- A passing static comparison can justify one new, separately authorized HIL
  attempt only if it distinguishes the packet/control path from previous runs.
- Work that produces no measurable benefit is recorded as such and closes its
  branch instead of accumulating retries.
- The register is an engineering decision record, not a source of hardware
  authority; existing preflight and explicit operator authorization remain
  mandatory.
