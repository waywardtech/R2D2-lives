from __future__ import annotations

from threading import Event
import time
import unittest

from r2_runtime.motion_watchdog import IndependentMotionWatchdog


class IndependentMotionWatchdogTest(unittest.TestCase):
    def test_blocked_worker_cannot_block_stop_deadline(self) -> None:
        release = Event()
        stop_called = Event()
        watchdog = IndependentMotionWatchdog(stop_called.set)

        result = watchdog.run(lambda: release.wait(2.0), timeout_s=0.05)
        release.set()

        self.assertEqual(result.terminal, "timed_out")
        self.assertTrue(result.stop_dispatched)
        self.assertTrue(stop_called.is_set())
        self.assertLess(result.elapsed_s, 0.3)

    def test_worker_failure_dispatches_exactly_one_stop(self) -> None:
        stops: list[float] = []
        watchdog = IndependentMotionWatchdog(lambda: stops.append(time.monotonic()))

        def fail() -> None:
            raise ConnectionError("injected private detail")

        result = watchdog.run(fail, timeout_s=0.2)
        self.assertEqual(result.terminal, "worker_failed")
        self.assertEqual(result.worker_error_type, "ConnectionError")
        self.assertEqual(len(stops), 1)

    def test_normal_completion_still_dispatches_final_stop_once(self) -> None:
        stops: list[str] = []
        watchdog = IndependentMotionWatchdog(lambda: stops.append("stop"))
        result = watchdog.run(lambda: None, timeout_s=0.2)
        self.assertEqual(result.terminal, "completed")
        self.assertEqual(stops, ["stop"])

    def test_stop_failure_is_sanitized_and_not_retried(self) -> None:
        calls = 0

        def stop() -> None:
            nonlocal calls
            calls += 1
            raise TimeoutError("private firmware detail")

        result = IndependentMotionWatchdog(stop).run(lambda: None, timeout_s=0.2)
        self.assertEqual(result.terminal, "stop_failed")
        self.assertEqual(result.stop_error_type, "TimeoutError")
        self.assertEqual(calls, 1)
        self.assertNotIn("private", str(result))

    def test_timeout_bounds_are_rejected_before_worker_start(self) -> None:
        started = False

        def operation() -> None:
            nonlocal started
            started = True

        for timeout in (0.0, 5.01):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                IndependentMotionWatchdog(lambda: None).run(operation, timeout_s=timeout)
        self.assertFalse(started)


if __name__ == "__main__":
    unittest.main()
