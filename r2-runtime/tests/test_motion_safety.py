from __future__ import annotations

from dataclasses import replace
import unittest

from r2_runtime.motion_safety import (
    BoundedMotionRequest,
    MotionLease,
    MotionSafetyExecutive,
)


class FakeDriver:
    def __init__(self) -> None:
        self.stop_count = 0

    def safe_hold(self) -> None:
        self.stop_count += 1


class MotionSafetyExecutiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 100.0
        self.driver = FakeDriver()
        self.safety = MotionSafetyExecutive(self.driver, monotonic=lambda: self.now)
        self.lease = MotionLease("lease-1", "operator-1", 99.0, 105.0)
        self.request = BoundedMotionRequest(
            command_id="cmd-1",
            idempotency_key="idem-1",
            lease_id="lease-1",
            controller_id="operator-1",
            distance_m=0.20,
            speed_mps=0.05,
            duration_s=4.0,
            deadline_monotonic_s=104.0,
        )

    def test_valid_request_is_accepted_once_under_exact_bounds(self) -> None:
        self.safety.arm(self.lease)
        first = self.safety.evaluate(self.request)
        duplicate = self.safety.evaluate(replace(self.request, distance_m=0.25))
        self.assertEqual(first.status, "accepted")
        self.assertEqual(duplicate, first)
        self.assertEqual(self.driver.stop_count, 0)

    def test_missing_expired_mismatched_and_stale_authority_are_rejected(self) -> None:
        self.assertEqual(self.safety.evaluate(self.request).reason, "motion_lease_missing")
        cases = (
            (replace(self.request, idempotency_key="expired"), 106.0, "motion_lease_expired"),
            (
                replace(self.request, idempotency_key="mismatch", lease_id="other"),
                100.0,
                "motion_lease_mismatch",
            ),
            (
                replace(self.request, idempotency_key="stale", deadline_monotonic_s=99.0),
                100.0,
                "command_stale",
            ),
        )
        for request, now, reason in cases:
            with self.subTest(reason=reason):
                safety = MotionSafetyExecutive(self.driver, monotonic=lambda now=now: now)
                safety.arm(self.lease if now < 105.0 else MotionLease("x", "x", 99.0, 110.0))
                if reason == "motion_lease_expired":
                    safety._lease = self.lease
                self.assertEqual(safety.evaluate(request).reason, reason)

    def test_every_bound_fails_closed_without_driver_motion(self) -> None:
        self.safety.arm(self.lease)
        cases = (
            ("distance", replace(self.request, idempotency_key="d", distance_m=0.251)),
            ("speed", replace(self.request, idempotency_key="s", speed_mps=0.051)),
            ("duration", replace(self.request, idempotency_key="t", duration_s=5.01)),
            (
                "kinematics",
                replace(
                    self.request,
                    idempotency_key="k",
                    distance_m=0.25,
                    speed_mps=0.04,
                    duration_s=5.0,
                ),
            ),
        )
        for _, request in cases:
            self.assertEqual(self.safety.evaluate(request).status, "rejected")
        self.assertEqual(self.driver.stop_count, 0)

    def test_watchdog_and_revoke_dispatch_safe_hold_once_each(self) -> None:
        self.safety.arm(self.lease)
        self.assertFalse(self.safety.watchdog_tick())
        self.now = 105.0
        self.assertTrue(self.safety.watchdog_tick())
        self.assertFalse(self.safety.watchdog_tick())
        self.safety.arm(MotionLease("lease-2", "operator-1", 105.0, 106.0))
        self.safety.revoke()
        self.assertEqual(self.driver.stop_count, 2)


if __name__ == "__main__":
    unittest.main()
