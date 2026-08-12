from __future__ import annotations

import unittest

from r2_runtime.system_status import assess_system_status, merge_droid_snapshot


class SystemStatusTest(unittest.TestCase):
    def test_highlights_thermal_throttle_memory_disk_service_and_clock_issues(self) -> None:
        issues = assess_system_status(
            {
                "clock": {"synchronized": False},
                "pi": {
                    "cpu_temperature_c": 81.0,
                    "throttling": "throttled=0x50000",
                    "memory": {"total_bytes": 100, "available_bytes": 9},
                    "disk": {"used_percent": 91.0},
                    "services": {"apache2": "inactive"},
                },
            }
        )
        self.assertEqual(
            {issue["code"] for issue in issues},
            {
                "pi_cpu_hot",
                "pi_throttled",
                "memory_low",
                "disk_low",
                "apache_inactive",
                "clock_unsynchronized",
            },
        )

    def test_absent_droid_is_explicit_information_not_a_health_failure(self) -> None:
        merged = merge_droid_snapshot({"issues": [], "overall": "nominal"}, None)
        self.assertEqual(merged["droid"]["status"], "unobserved")
        self.assertEqual(merged["issues"][0]["severity"], "info")
        self.assertEqual(merged["overall"], "nominal")

    def test_droid_failure_and_unsafe_state_are_critical_issues(self) -> None:
        merged = merge_droid_snapshot(
            {"issues": [], "overall": "nominal"},
            {
                "expression": {"status": "failed"},
                "battery": {"state": "critical"},
                "safe_hold": False,
            },
        )
        self.assertEqual(merged["overall"], "attention")
        self.assertEqual(
            {issue["code"] for issue in merged["issues"]},
            {
                "droid_expression_failed",
                "droid_battery_unsafe",
                "droid_safe_hold_unconfirmed",
            },
        )


if __name__ == "__main__":
    unittest.main()
