"""Single serialized owner for the R2 BLE adapter."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Callable, TypeVar

from .drivers import Spherov2R2Driver

T = TypeVar("T")


class ConnectionState(str, Enum):
    OFFLINE = "offline"
    CONNECTING = "connecting"
    PROBING = "probing"
    READY = "ready"
    DEGRADED = "degraded"
    DISCONNECTING = "disconnecting"


@dataclass(frozen=True)
class OwnerEvent:
    sequence: int
    state: ConnectionState
    reason: str


class BleOwner:
    """The only class permitted to call the low-level driver lifecycle."""

    def __init__(
        self,
        driver: Spherov2R2Driver,
        *,
        event_sink: Callable[[OwnerEvent], None] | None = None,
    ) -> None:
        self._driver = driver
        self._command_lock = Lock()
        self._state = ConnectionState.OFFLINE
        self._events: list[OwnerEvent] = []
        self._event_sink = event_sink
        self._event_sink_failed = False
        self._append_event(self._state, "startup_safe_hold")

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def stopped(self) -> bool:
        return self._driver.stopped

    @property
    def events(self) -> tuple[OwnerEvent, ...]:
        return tuple(self._events)

    @property
    def event_sink_failed(self) -> bool:
        return self._event_sink_failed

    def _append_event(self, state: ConnectionState, reason: str) -> None:
        event = OwnerEvent(len(self._events) + 1, state, reason)
        self._events.append(event)
        if self._event_sink is not None:
            try:
                self._event_sink(event)
            except Exception:
                # Observability must never interrupt stop/disconnect processing.
                self._event_sink_failed = True

    def _transition(self, state: ConnectionState, reason: str) -> None:
        self._state = state
        self._append_event(state, reason)

    def connect_for_stationary_probe(self) -> None:
        with self._command_lock:
            self._transition(ConnectionState.CONNECTING, "stationary_probe")
            try:
                self._driver.connect()
            except Exception:
                self._driver.stopped = True
                self._transition(ConnectionState.OFFLINE, "connect_failed_safe")
                raise
            self._transition(ConnectionState.PROBING, "connected_stopped")

    def mark_ready(self) -> None:
        if not self._driver.stopped:
            raise RuntimeError("cannot mark ready unless driver is stopped")
        self._transition(ConnectionState.READY, "stationary_probe_complete")

    def serialized(self, operation: Callable[[], T]) -> T:
        with self._command_lock:
            return operation()

    def disconnect(self, reason: str = "requested") -> None:
        with self._command_lock:
            self._transition(ConnectionState.DISCONNECTING, reason)
            try:
                self._driver.disconnect()
            finally:
                self._driver.stopped = True
                self._transition(ConnectionState.OFFLINE, "disconnected_safe_hold")

    def link_lost(self) -> None:
        with self._command_lock:
            self._driver.stopped = True
            self._driver.connected = False
            self._transition(ConnectionState.OFFLINE, "link_lost_no_resume")
