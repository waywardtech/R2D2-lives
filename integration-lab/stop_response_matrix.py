"""Run the deterministic, non-BLE stop-response trace matrix."""

from __future__ import annotations

import json

from r2_runtime.stop_trace_sim import stop_response_matrix


def main() -> None:
    print(json.dumps(stop_response_matrix(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
