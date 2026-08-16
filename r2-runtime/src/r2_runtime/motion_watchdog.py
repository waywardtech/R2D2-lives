"""Independent motion watchdog that does not share the command worker's lock."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event, Lock, Thread
import time
from typing import Callable, Literal


@dataclass(frozen=True)
class WatchdogResult:
    terminal: Literal["completed", "worker_failed", "timed_out", "stop_failed"]
    stop_dispatched: bool
    stop_error_type: str | None
    worker_error_type: str | None
    elapsed_s: float


class IndependentMotionWatchdog:
    """Runs one command while a separate thread owns the stop deadline."""

    def __init__(
        self,
        stop_dispatcher: Callable[[], None],
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._stop_dispatcher = stop_dispatcher
        self._monotonic = monotonic
        self._stop_lock = Lock()
        self._stop_dispatched = False
        self._stop_error: Exception | None = None

    def _dispatch_stop_once(self) -> None:
        with self._stop_lock:
            if self._stop_dispatched:
                return
            self._stop_dispatched = True
        try:
            self._stop_dispatcher()
        except Exception as error:
            self._stop_error = error

    def run(self, operation: Callable[[], None], *, timeout_s: float) -> WatchdogResult:
        if not 0.05 <= timeout_s <= 5.0:
            raise ValueError("motion watchdog timeout must be in [0.05, 5.0] seconds")
        started = self._monotonic()
        worker_done = Event()
        watchdog_cancel = Event()
        worker_error: list[Exception] = []

        def worker() -> None:
            try:
                operation()
            except Exception as error:
                worker_error.append(error)
                self._dispatch_stop_once()
            finally:
                worker_done.set()

        def watchdog() -> None:
            if not watchdog_cancel.wait(timeout_s):
                self._dispatch_stop_once()

        worker_thread = Thread(target=worker, name="r2-motion-worker", daemon=True)
        watchdog_thread = Thread(target=watchdog, name="r2-stop-watchdog", daemon=False)
        worker_thread.start()
        watchdog_thread.start()
        completed_before_deadline = worker_done.wait(timeout_s)
        if completed_before_deadline:
            watchdog_cancel.set()
            self._dispatch_stop_once()
        watchdog_thread.join(timeout=timeout_s + 0.1)
        if watchdog_thread.is_alive():
            self._dispatch_stop_once()
            watchdog_thread.join(timeout=0.1)

        elapsed = max(0.0, self._monotonic() - started)
        if self._stop_error is not None:
            terminal: Literal["completed", "worker_failed", "timed_out", "stop_failed"] = (
                "stop_failed"
            )
        elif worker_error:
            terminal = "worker_failed"
        elif not completed_before_deadline:
            terminal = "timed_out"
        else:
            terminal = "completed"
        return WatchdogResult(
            terminal=terminal,
            stop_dispatched=self._stop_dispatched,
            stop_error_type=(type(self._stop_error).__name__ if self._stop_error else None),
            worker_error_type=(type(worker_error[0]).__name__ if worker_error else None),
            elapsed_s=elapsed,
        )
