"""One bounded, stationary proof-of-life expression plus a complete status report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Mapping

from .ble_owner import BleOwner
from .drivers import Spherov2R2Driver
from .encounter_session import SAFE_BATTERY_STATES
from .encounters import StationaryExpressionPlan, proof_of_life_plan
from .system_status import collect_system_status, merge_droid_snapshot


class ProofOfLifeSessionError(RuntimeError):
    """Sanitized primary failure plus optional disconnect uncertainty."""

    def __init__(
        self,
        phase: str,
        error_type: str,
        *,
        cleanup_error_type: str | None = None,
    ) -> None:
        super().__init__(f"proof of life failed during {phase}")
        self.phase = phase
        self.error_type = error_type
        self.cleanup_error_type = cleanup_error_type


@dataclass(frozen=True)
class ProofOfLifeReport:
    seed: int
    plan: StationaryExpressionPlan
    status: Mapping[str, object]
    final_state: str
    movement_performed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "evidence_category": "stationary-proof-of-life",
            "seed": self.seed,
            "plan": asdict(self.plan),
            "status": dict(self.status),
            "final_state": self.final_state,
            "movement_performed": self.movement_performed,
        }


def run_proof_of_life(
    owner: BleOwner,
    driver: Spherov2R2Driver,
    *,
    seed: int,
    system_collector: Callable[[], dict[str, object]] = collect_system_status,
    stage_sink: Callable[[str, Mapping[str, object]], None] | None = None,
) -> ProofOfLifeReport:
    def mark(stage: str, detail: Mapping[str, object] | None = None) -> None:
        if stage_sink is not None:
            stage_sink(stage, detail or {})

    plan = proof_of_life_plan(seed)
    phase = "system_status_collection"
    host_status = system_collector()
    mark("system_status_collected")
    droid_status: dict[str, object] = {
        "connection": "offline",
        "safe_hold": True,
        "movement_performed": False,
    }
    mark("connect_started")
    primary_failure: tuple[str, Exception] | None = None
    disconnect_failure: Exception | None = None
    try:
        phase = "connect"
        owner.connect_for_stationary_probe()
        mark("connect_completed")
        droid_status["connection"] = owner.state.value
        phase = "identity_query"
        droid_status["identity"] = dict(owner.serialized(driver.backend.identity))
        mark("identity_checked")
        phase = "battery_query"
        battery = dict(owner.serialized(driver.backend.battery))
        droid_status["battery"] = battery
        battery_state = str(battery.get("state", "unknown")).lower()
        battery_safe = battery_state in SAFE_BATTERY_STATES
        mark("battery_checked", {"battery_safe": battery_safe})
        if not battery_safe:
            raise PermissionError(f"battery state {battery_state!r} blocks proof of life")
        phase = "head_position_query"
        droid_status["head"] = dict(
            owner.serialized(lambda: driver.backend.exercise_stationary("head.safe_range"))
        )
        mark("head_checked")
        mark("expression_started")
        phase = "stationary_expression"
        owner.perform_stationary_expression(plan)
        mark("expression_completed")
        phase = "ready_transition"
        owner.mark_ready()
        droid_status["expression"] = {
            "status": "completed",
            "semantic": plan.semantic,
            "audio_name": plan.audio_name,
            "head_restored": True,
            "logic_displays_off": True,
            "audio_stopped": True,
        }
    except Exception as error:
        primary_failure = (phase, error)
        mark("session_failed")
    finally:
        mark("disconnect_started")
        try:
            owner.disconnect("proof_of_life_complete")
        except Exception as error:
            disconnect_failure = error
        else:
            mark("disconnect_completed")
        droid_status["connection"] = owner.state.value
        droid_status["safe_hold"] = owner.stopped
    if primary_failure is not None:
        failure_phase, original_failure = primary_failure
        if hasattr(original_failure, "phase"):
            failure_phase = f"{failure_phase}.{original_failure.phase}"
        raise ProofOfLifeSessionError(
            failure_phase,
            getattr(original_failure, "error_type", type(original_failure).__name__),
            cleanup_error_type=(
                type(disconnect_failure).__name__ if disconnect_failure is not None else None
            ),
        ) from original_failure
    if disconnect_failure is not None:
        raise ProofOfLifeSessionError(
            "disconnect", type(disconnect_failure).__name__
        ) from disconnect_failure
    mark("session_completed")
    status = merge_droid_snapshot(host_status, droid_status)
    return ProofOfLifeReport(seed, plan, status, owner.state.value)
