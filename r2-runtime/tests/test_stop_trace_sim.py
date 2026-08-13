from __future__ import annotations

import json
import unittest

from r2_runtime.stop_trace_sim import stop_response_matrix


class StopTraceSimulationTest(unittest.TestCase):
    def test_matrix_is_deterministic_non_actuating_and_fail_closed(self) -> None:
        first = stop_response_matrix()
        second = stop_response_matrix()
        self.assertEqual(first, second)
        self.assertFalse(first["hardware_accessed"])
        self.assertFalse(first["movement_performed"])
        outcomes = {item["scenario"]: item["outcome"] for item in first["results"]}
        self.assertEqual(outcomes["acknowledged_success"], "acknowledged_success")
        self.assertEqual(outcomes["acknowledged_firmware_error"], "acknowledged_error")
        self.assertEqual(outcomes["response_timeout"], "stop_unconfirmed")
        self.assertEqual(outcomes["cleanup_failure"], "invalid_test")
        self.assertTrue(outcomes["sequence_mismatch"].startswith("rejected:"))
        serialized = json.dumps(first)
        for forbidden in ("bluetooth", "address", "identity", "private"):
            self.assertNotIn(forbidden, serialized.casefold())


if __name__ == "__main__":
    unittest.main()
