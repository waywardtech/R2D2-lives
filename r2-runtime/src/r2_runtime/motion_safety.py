"""Deterministic motion authorization; no vendor or model dependency."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Callable, Literal, Protocol


class SafeHoldDriver(Protocol):
    def safe_hold(self) -> None: ...


@dataclass(frozen=True)
class MotionLimits:
    max_distance_m: float = 0.25
    max_speed_mps: float = 0.05
    max_duration_s: float = 5.0

    def __post_init__(self) -> None:
        if not 0 < self.max_distance_m <= 0.25:
            raise ValueError("maximum distance must be in (0, 0.25] m")
        if not 0 < self.max_speed_mps <= 0.05:
            raise ValueError("maximum speed must be in (0, 0.05] m/s")
        if not 0 < self.max_duration_s <= 5.0:
            raise ValueError("maximum duration must be in (0, 5] s")


@dataclass(frozen=True)
class MotionLease:
    lease_id: str
    controller_id: str
    issued_monotonic_s: float
    expires_monotonic_s: float

    def __post_init__(self) -> None:
        if not self.lease_id or not self.controller_id:
            raise ValueError("lease and controller IDs are required")
        if self.expires_monotonic_s <= self.issued_monotonic_s:
            raise ValueError("motion lease expiry must follow issuance")


@dataclass(frozen=True)
class BoundedMotionRequest:
    command_id: str
    idempotency_key: str
    lease_id: str
    controller_id: str
    distance_m: float
    speed_mps: float
    duration_s: float
    deadline_monotonic_s: float


@dataclass(frozen=True)
class MotionDecision:
    status: Literal["accepted", "rejected"]
    reason: str


class MotionSafetyExecutive:
    """Owns lease validation, duplicate suppression, and watchdog safe-hold."""

    def __init__(
        self,
        driver: SafeHoldDriver,
        *,
        limits: MotionLimits | None = None,
        monotonic: Callable[[], float],
    ) -> None:
        self._driver = driver
        self._limits = limits or MotionLimits()
        self._monotonic = monotonic
        self._lease: MotionLease | None = None
        self._seen: dict[str, MotionDecision] = {}
        self._lock = Lock()

    def arm(self, lease: MotionLease) -> None:
        with self._lock:
            if lease.expires_monotonic_s <= self._monotonic():
                raise ValueError("cannot arm an expired motion lease")
            self._lease = lease

    def evaluate(self, request: BoundedMotionRequest) -> MotionDecision:
        with self._lock:
            prior = self._seen.get(request.idempotency_key)
            if prior is not None:
                return prior
            decision = self._evaluate_new(request, self._monotonic())
            self._seen[request.idempotency_key] = decision
            return decision

    def _evaluate_new(self, request: BoundedMotionRequest, now: float) -> MotionDecision:
        lease = self._lease
        if lease is None:
            return MotionDecision("rejected", "motion_lease_missing")
        if now >= lease.expires_monotonic_s:
            return MotionDecision("rejected", "motion_lease_expired")
        if request.deadline_monotonic_s <= now:
            return MotionDecision("rejected", "command_stale")
        if (request.lease_id, request.controller_id) != (lease.lease_id, lease.controller_id):
            return MotionDecision("rejected", "motion_lease_mismatch")
        if not 0 < request.distance_m <= self._limits.max_distance_m:
            return MotionDecision("rejected", "distance_out_of_bounds")
        if not 0 < request.speed_mps <= self._limits.max_speed_mps:
            return MotionDecision("rejected", "speed_out_of_bounds")
        if not 0 < request.duration_s <= self._limits.max_duration_s:
            return MotionDecision("rejected", "duration_out_of_bounds")
        if request.distance_m > request.speed_mps * request.duration_s:
            return MotionDecision("rejected", "kinematic_bound_inconsistent")
        return MotionDecision("accepted", "bounded_motion_authorized")

    def watchdog_tick(self) -> bool:
        """Safe-hold once on lease expiry; returns whether stop was dispatched."""
        with self._lock:
            if self._lease is None or self._monotonic() < self._lease.expires_monotonic_s:
                return False
            self._lease = None
        self._driver.safe_hold()
        return True

    def revoke(self) -> None:
        with self._lock:
            self._lease = None
        self._driver.safe_hold()
