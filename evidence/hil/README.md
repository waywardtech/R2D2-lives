# HIL evidence

This directory contains immutable, sanitized hardware-in-the-loop reports.
Never store BLE addresses, configured advertised names, credentials, or other
device-discovery output here. A failed report remains evidence and must not be
overwritten by a later run.

`proof-of-life-attempt-1-failure.json` and its progress journal preserve the
single authorized 2026-08-12 proof-of-life failure. The journal reached a safe
battery result but not `head_checked` or `expression_started`; no LED, sound,
dome-set, or locomotion primitive was issued. Cleanup did not record
`disconnect_completed`, so the external watchdog terminated the lingering
process and controller power-off supplied the externally observed link cleanup.
