"""Stationary, deterministic capability probing and evidence reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Mapping

from .ble_owner import BleOwner
from .drivers import Spherov2R2Driver

STATIONARY_CAPABILITIES = (
    "identity.system_info",
    "battery.state_voltage",
    "led.low_brightness",
    "head.safe_range",
    "audio.quiet_preview",
    "telemetry.stationary",
    "collision.configuration",
)
MOVEMENT_CAPABILITIES = ("drive.bounded", "stop.latency", "locator.motion_calibration")


@dataclass(frozen=True)
class CapabilityEvidence:
    status: str
    detail: Mapping[str, object]


@dataclass(frozen=True)
class CapabilityReport:
    schema_version: str
    evidence_category: str
    generated_at: str
    device_ref: str
    library_baseline: str
    firmware: Mapping[str, str]
    capabilities: Mapping[str, CapabilityEvidence]
    movement_performed: bool
    final_state: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def sha256(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()


def _device_ref(identity: Mapping[str, str]) -> str:
    public_parts = (identity.get("model", "unknown"), identity.get("system", "unknown"))
    return "sha256:" + hashlib.sha256("|".join(public_parts).encode()).hexdigest()


class StationaryCapabilityProbe:
    def __init__(self, owner: BleOwner, driver: Spherov2R2Driver) -> None:
        self.owner = owner
        self.driver = driver

    def run(self, *, generated_at: str | None = None, evidence_category: str = "simulation") -> CapabilityReport:
        self.owner.connect_for_stationary_probe()
        evidence: dict[str, CapabilityEvidence] = {}
        identity: Mapping[str, str] = {}
        try:
            identity = self.owner.serialized(self.driver.backend.identity)
            observed_status = "simulated" if evidence_category == "simulation" else "observed"
            evidence["identity.system_info"] = CapabilityEvidence(observed_status, dict(identity))
            battery = self.owner.serialized(self.driver.backend.battery)
            evidence["battery.state_voltage"] = CapabilityEvidence(observed_status, dict(battery))
            battery_state = str(battery.get("state", "unknown")).lower()
            battery_blocks_actions = (
                evidence_category != "simulation"
                and battery_state not in {"ok", "charged", "charging", "not_charging"}
            )
            for capability in STATIONARY_CAPABILITIES[2:]:
                if battery_blocks_actions:
                    evidence[capability] = CapabilityEvidence(
                        "untested",
                        {"reason": f"battery state {battery_state!r} blocks hardware actions"},
                    )
                    continue
                try:
                    detail = self.owner.serialized(
                        lambda capability=capability: self.driver.backend.exercise_stationary(capability)
                    )
                except PermissionError as exc:
                    evidence[capability] = CapabilityEvidence(
                        "untested", {"reason": str(exc)}
                    )
                else:
                    evidence[capability] = CapabilityEvidence(observed_status, dict(detail))
            for capability in MOVEMENT_CAPABILITIES:
                evidence[capability] = CapabilityEvidence(
                    "untested", {"reason": "requires separately authorized motion HIL"}
                )
            self.driver.safe_hold()
            self.owner.mark_ready()
        finally:
            self.owner.disconnect("stationary_probe_complete")
        timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return CapabilityReport(
            schema_version="1.0",
            evidence_category=evidence_category,
            generated_at=timestamp,
            device_ref=_device_ref(identity),
            library_baseline=self.driver.expected_library_version,
            firmware={
                "model": identity.get("model", "unknown"),
                "system": identity.get("system", "unknown"),
                "firmware": identity.get("firmware", "unknown"),
            },
            capabilities=evidence,
            movement_performed=False,
            final_state="safe_hold",
        )
