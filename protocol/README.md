# SAP protocol package

This independently buildable package contains the versioned SAP 0.1.0 schemas,
generated boundary types/clients, validation helpers, fixtures, and conformance
tests. Runtime code uses only Python's standard library. Run
`python ../scripts/tasks.py contract` from the workspace root.

The generated file is reproducible with `python tools/generate_clients.py`; CI
uses `--check` to reject drift. Unknown additive fields are retained in the
`extensions` mapping on generated boundary records.

