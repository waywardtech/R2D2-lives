# Evidence-gated delivery

R2 Runtime follows [ADR-005](../specs/decisions/ADR-005-evidence-gated-delivery.md):
we build or deploy a new behavior only when it has a measurable benefit over a
recorded baseline. The machine-checked register is
[`planning/benefit-register.json`](../planning/benefit-register.json).

## Working loop

1. Research authoritative sources first; label upstream and community material
   as supporting evidence, not product authority.
2. Record the baseline, measurable outcome, threshold, method, and stop rule.
3. Build the smallest simulation/static check that can disprove the hypothesis.
4. Deploy only a verified, isolated release with a rollback path.
5. Use hardware only after a distinct hypothesis, fresh explicit authorization,
   the existing physical preflight, and an operator-observable measurement.
6. Record either benefit or no benefit. Do not retry an unchanged no-benefit
   path.

## R201 locomotion decision

The secondary-processor/tripod diagnostic had a bounded safe completion but no
observed wheel motion. The subsequent static parity audit found two control-path
differences: upstream R2 raw-motor/heading bindings retain their default
processor, while the diagnostic explicitly targeted the secondary processor.
This is a research benefit, not a locomotion success. It rules out treating the
secondary selection as an improvement and blocks another duration, speed, or
packet retry without a new hypothesis.

The research basis is limited and explicit:

- Sphero’s public API defines raw-motor modes/speeds and notes that packets can
  target particular nodes. It does not publish an R201-specific wheel-control
  recipe. [Sphero SDK documents](https://sites.google.com/sphero.com/sphero-public-sdk/documentation/sdk-documents)
  and [API protocol documents](https://sdk.sphero.com/documentation/api-documents)
- The upstream `spherov2.py` project supports R2-D2/R2-Q5 and recommends its
  high-level API over its undocumented per-toy methods. [Upstream project](https://github.com/artificial-intelligence-class/spherov2.py)
- A community R2 wrapper models tripod stance as required for rolling, but that
  claim is supporting evidence only until validated on this specific R201.
  [Community wrapper source](https://github.com/ccb/sphero-r2d2/blob/main/spherov2/sphero_edu.py)

No source above authorizes hardware activity or overrides the project’s safety
executive, preflight, or operator authority.
