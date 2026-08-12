from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol

from .encounters import StationaryExpressionPlan


class DroidDriver(Protocol):
    def safe_hold(self) -> None: ...


class HardwareUnavailableError(RuntimeError):
    pass


class Spherov2Backend(Protocol):
    """Narrow reviewed surface over the pinned third-party BLE library."""

    @property
    def library_version(self) -> str: ...

    def connect(self, configured_identity: str) -> None: ...
    def disconnect(self) -> None: ...
    def stop(self) -> None: ...
    def identity(self) -> Mapping[str, str]: ...
    def battery(self) -> Mapping[str, object]: ...
    def exercise_stationary(self, capability: str) -> Mapping[str, object]: ...
    def discover_nearby_droids(self, configured_identity: str) -> tuple[str, ...]: ...
    def perform_stationary_expression(self, plan: StationaryExpressionPlan) -> None: ...


class UnavailableSpherov2Backend:
    library_version = "unavailable"

    def _raise(self) -> None:
        raise HardwareUnavailableError(
            "spherov2.py backend is not installed; simulation/replay is mandatory"
        )

    def connect(self, configured_identity: str) -> None:
        self._raise()

    def disconnect(self) -> None:
        self._raise()

    def stop(self) -> None:
        self._raise()

    def identity(self) -> Mapping[str, str]:
        self._raise()
        return {}

    def battery(self) -> Mapping[str, object]:
        self._raise()
        return {}

    def exercise_stationary(self, capability: str) -> Mapping[str, object]:
        self._raise()
        return {}

    def discover_nearby_droids(self, configured_identity: str) -> tuple[str, ...]:
        self._raise()
        return ()

    def perform_stationary_expression(self, plan: StationaryExpressionPlan) -> None:
        self._raise()


@dataclass
class Spherov2R2Driver:
    """Owned adapter for the pinned 0.12.1 baseline; no raw types escape."""

    backend: Spherov2Backend = field(default_factory=UnavailableSpherov2Backend)
    configured_identity: str = ""
    connected: bool = False
    stopped: bool = True
    stop_attempted_since_connect: bool = False
    transport_failed: bool = False

    expected_library_version = "0.12.1"

    def connect(self) -> None:
        if not self.configured_identity:
            raise ValueError("configured droid identity is required outside source control")
        if isinstance(self.backend, UnavailableSpherov2Backend):
            self.backend.connect(self.configured_identity)
        if self.backend.library_version != self.expected_library_version:
            raise RuntimeError(
                f"expected spherov2.py {self.expected_library_version}, "
                f"got {self.backend.library_version}"
            )
        try:
            self.backend.connect(self.configured_identity)
        except Exception:
            try:
                self.backend.stop()
            except Exception:
                pass
            try:
                self.backend.disconnect()
            except Exception:
                pass
            self.connected = False
            self.stopped = True
            raise
        self.connected = True
        self.stopped = True
        self.stop_attempted_since_connect = False
        self.transport_failed = False

    def safe_hold(self) -> None:
        if not self.connected:
            self.stopped = True
            return
        self.stop_attempted_since_connect = True
        try:
            self.backend.stop()
        except Exception:
            self.stopped = False
            raise
        self.stopped = True

    def discover_nearby_droids(self) -> tuple[str, ...]:
        if self.connected:
            raise RuntimeError("nearby-droid scan requires an offline R2 connection")
        return self.backend.discover_nearby_droids(self.configured_identity)

    def perform_stationary_expression(self, plan: StationaryExpressionPlan) -> None:
        if not self.connected or not self.stopped:
            raise RuntimeError("stationary expression requires a connected, stopped R2")
        try:
            self.backend.perform_stationary_expression(plan)
        except (EOFError, ConnectionError):
            self.transport_failed = True
            self.stopped = True
            raise
        except Exception as error:
            if isinstance(error.__cause__, (EOFError, ConnectionError)):
                self.transport_failed = True
                self.stopped = True
            raise

    def disconnect(self) -> None:
        if self.connected:
            try:
                if not self.stop_attempted_since_connect and not self.transport_failed:
                    self.safe_hold()
            finally:
                try:
                    self.backend.disconnect()
                finally:
                    self.connected = False
                    self.stopped = True
                    self.stop_attempted_since_connect = False
                    self.transport_failed = False


@dataclass
class SimDroidDriver:
    """A deterministic driver with no BLE or hardware code path."""

    stopped: bool = True
    history: list[str] = field(default_factory=list)

    def safe_hold(self) -> None:
        self.stopped = True
        self.history.append("safe_hold")
