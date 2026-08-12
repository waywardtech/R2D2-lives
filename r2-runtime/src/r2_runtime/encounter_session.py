"""Stationary-only orchestration for privacy-safe nearby-droid reactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .ble_owner import BleOwner, ConnectionState
from .drivers import Spherov2R2Driver
from .encounters import DroidEncounterChat, DroidEncounterReaction

SAFE_BATTERY_STATES = frozenset({"ok", "charged", "charging", "not_charging"})


@dataclass(frozen=True)
class DroidEncounterReport:
    observed_droid_kinds: tuple[str, ...]
    reactions: tuple[DroidEncounterReaction, ...]
    final_state: str
    movement_performed: bool = False
    device_identity_persisted: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "evidence_category": "stationary-droid-encounter",
            "observed_droid_kinds": self.observed_droid_kinds,
            "reactions": tuple(reaction.to_dict() for reaction in self.reactions),
            "final_state": self.final_state,
            "movement_performed": self.movement_performed,
            "device_identity_persisted": self.device_identity_persisted,
        }


def run_droid_encounter_session(
    owner: BleOwner,
    driver: Spherov2R2Driver,
    chat: DroidEncounterChat,
    *,
    max_reactions: int = 3,
) -> DroidEncounterReport:
    if not 1 <= max_reactions <= 5:
        raise ValueError("max reactions must be in [1, 5]")
    observed = owner.discover_nearby_droids()
    if not observed:
        return DroidEncounterReport((), (), ConnectionState.OFFLINE.value)

    reactions: list[DroidEncounterReaction] = []
    owner.connect_for_stationary_probe()
    try:
        battery: Mapping[str, object] = owner.serialized(driver.backend.battery)
        battery_state = str(battery.get("state", "unknown")).lower()
        if battery_state not in SAFE_BATTERY_STATES:
            raise PermissionError(f"battery state {battery_state!r} blocks stationary expressions")
        for index in range(max_reactions):
            kind = observed[index % len(observed)]
            reaction = chat.plan(kind, index + 1)
            owner.perform_stationary_expression(reaction.plan)
            reactions.append(reaction)
        owner.mark_ready()
    finally:
        owner.disconnect("stationary_droid_encounter_complete")
    return DroidEncounterReport(observed, tuple(reactions), owner.state.value)
