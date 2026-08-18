# R201 stock-primary carpet-tile calibration

`scripts/hil_stock_bounded_calibration.py` is a one-shot hardware calibration
aid for the R201 control path that produced observed locomotion. It is not
available to the PWA, conversation service, or SAP.

The test uses the reviewed upstream default processor with speed 25 for 0.10 s,
after the normal three-leg wake settle. An independent 0.25 s watchdog queues
OFF/0 and the runner returns R2 to two legs before disconnecting.

The evidence is specific to 8-inch carpet tiles. It must never be generalized
to wood, concrete, or another surface. Before invoking it, place fixed start
and 0.25 m maximum-distance marks, keep the droid physically contained, and
retain immediate emergency disconnect access. The operator records the measured
forward displacement, direction, final stance, and abnormal behavior. A script
completion proves queueing and safe disconnect only; it does not prove speed,
stopping distance, or physical-stop effectiveness.
