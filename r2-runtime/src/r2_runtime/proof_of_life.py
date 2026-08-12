"""One bounded, stationary proof-of-life expression plus a complete status report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Mapping

from .ble_owner import BleOwner
from .drivers import Spherov2R2Driver
from .encounter_session import SAFE_BATTERY_STATES
from .encounters import StationaryExpressionPlan, proof_of_life_plan
from .system_status import collect_system_status, merge_droid_snapshot


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
    host_status = system_collector()
    mark("system_status_collected")
    droid_status: dict[str, object] = {
        "connection": "offline",
        "safe_hold": True,
        "movement_performed": False,
    }
    mark("connect_started")
    try:
        owner.connect_for_stationary_probe()
        mark("connect_completed")
        droid_status["connection"] = owner.state.value
        droid_status["identity"] = dict(owner.serialized(driver.backend.identity))
        mark("identity_checked")
        battery = dict(owner.serialized(driver.backend.battery))
        droid_status["battery"] = battery
        battery_state = str(battery.get("state", "unknown")).lower()
        battery_safe = battery_state in SAFE_BATTERY_STATES
        mark("battery_checked", {"battery_safe": battery_safe})
        if not battery_safe:
            raise PermissionError(f"battery state {battery_state!r} blocks proof of life")
        droid_status["head"] = dict(
            owner.serialized(lambda: driver.backend.exercise_stationary("head.safe_range"))
        )
        mark("head_checked")
        mark("expression_started")
        owner.perform_stationary_expression(plan)
        mark("expression_completed")
        owner.mark_ready()
        droid_status["expression"] = {
            "status": "completed",
            "semantic": plan.semantic,
            "audio_name": plan.audio_name,
            "head_restored": True,
            "logic_displays_off": True,
            "audio_stopped": True,
        }
    except Exception:
        mark("session_failed")
        raise
    finally:
        mark("disconnect_started")
        owner.disconnect("proof_of_life_complete")
        mark("disconnect_completed")
        droid_status["connection"] = owner.state.value
        droid_status["safe_hold"] = owner.stopped
    mark("session_completed")
    status = merge_droid_snapshot(host_status, droid_status)
    return ProofOfLifeReport(seed, plan, status, owner.state.value)
