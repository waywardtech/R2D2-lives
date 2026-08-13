# R201 stop-response bench result: release 3855d7c

Date: 2026-08-13  
Evidence category: stationary HIL failure  
Result: `invalid_test`

The operator confirmed the complete physical preflight and separately issued the
immediate final authorization for exactly one raw-motor `OFF/0` packet. The
runner recorded one transmitted DID 22/CID 1 packet and no response observation.
The vendor path ended with `EOFError`; no retry occurred. Cleanup reported the
owner offline and zero BLE connections. Bluetooth was then soft-blocked.

After disconnection, the operator reported `PHYSICAL_NORMAL`: no unexpected
wheel activity or heading, direction, or location change, and R2 was stationary,
silent, undamaged, and otherwise normal. This observation does not alter the
immutable artifact's `physical_state: unconfirmed`, because the deterministic
policy accepts post-run confirmation only for success or the expected timeout
case. An `EOFError` therefore remains `invalid_test` and cannot establish a
firmware acknowledgement.

The immutable sanitized artifact is
`evidence/hil/stop-response-3855d7c.json`, SHA-256
`b531bd9f169629a020c865896cbb06eb512f8404ef42dc47c84ee0403fcbb836`.
It contains no advertised identity, BLE address, hostname, credentials, or raw
packet bytes. The private configured identity remains outside Git.

No retry is authorized. The response-path question remains unresolved and any
future physical attempt requires a fresh preflight, explicit authorization, and
immediate final go.
