# R201 bounded-motion calibration pulse

`scripts/hil_bounded_motion_calibration.py` is a single-use, separately armed
hardware calibration aid. It is not part of the runtime command surface and it
is never invoked by the web application, conversation system, or SAP.

The runner sends exactly one queue-only raw-motor forward pulse at speed 5 for
0.10 seconds. An independent watchdog queues raw-motor `OFF/0` on normal
completion, worker failure, or a 0.25-second deadline. The command path does
not wait for a firmware response. The final evidence therefore records requested
bounds and a queued (unacknowledged) stop, not an inferred distance or braking
claim.

It refuses before creating a BLE backend unless all of the following are supplied:

- exact motion-calibration authorization;
- visible operator, inspection, 0–40 C envelope, clear one-metre keep-out, and
  an immediately reachable emergency stop;
- unplugged charger, physical containment, a second confirmation, and explicit
  acknowledgement that the R201 wake sequence changes stance;
- external device identity and exact, non-source-controlled arm token.

The operator must measure and record the observed displacement, direction,
normal final state, and any unexpected behavior after the pulse. A successful
script result proves only local queueing and safe disconnect, not a calibrated
speed, stopping distance, or Phase 1 movement gate.

## Follow-up after no observed movement

The two initial speed-5 pulses were issued immediately after `wake()` and did
not produce observed displacement. `scripts/hil_post_wake_motion_diagnostic.py`
is therefore a distinct, newly armed diagnostic: it waits three seconds for the
wake/stance sequence, then sends one speed-10 pulse for 0.10 seconds under the
same independent stop watchdog. It requires its own exact authorization and arm
token; it is not a retry of the original calibration command.

## R2-specific secondary-processor diagnostic

The next separately armed diagnostic remains limited to one low-speed,
0.10-second forward request at speed 25 and the same 0.25-second independent
watchdog. It differs from the earlier generic raw-motor and heading attempts in
two documented R201 details:

- it queues the R2 `THREE_LEGS` animatronic action before the motion request and
  queues `TWO_LEGS` only after the watchdog has queued the stop;
- it sends Drive DID 22 control packets to the R2 secondary processor, including
  the paired R2 generic drive-motor CID 11 commands and the raw `OFF/0` stop.

The runner is `scripts/hil_speed_threshold_diagnostic.py`. It never waits for a
firmware response, it never retries, and it records only that its stop was
queued. The operator must still observe and record displacement, final stance,
LED/audio behavior, and the final stationary state. A completed script cannot
by itself prove that a motor packet was accepted or that the Phase 1 locomotion
gate passed.
