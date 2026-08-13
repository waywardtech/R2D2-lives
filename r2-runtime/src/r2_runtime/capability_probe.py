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


class CapabilityProbeError(RuntimeError):
    """Sanitized probe phase failure with separately retained cleanup status."""

    def __init__(
        self,
        phase: str,
        error_type: str,
        *,
        cleanup_error_type: str | None = None,
    ) -> None:
        super().__init__(f"stationary capability probe failed during {phase}")
        self.phase = phase
        self.error_type = error_type
        self.cleanup_error_type = cleanup_error_type


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

    def run(
        self, *, generated_at: str | None = None, evidence_category: str = "simulation"
    ) -> CapabilityReport:
        evidence: dict[str, CapabilityEvidence] = {}
        identity: Mapping[str, str] = {}
        final_state = "safe_hold"
        phase = "connect"
        primary_failure: tuple[str, Exception] | None = None
        disconnect_failure: Exception | None = None
        try:
            self.owner.connect_for_stationary_probe()
            phase = "identity.system_info"
            identity = self.owner.serialized(self.driver.backend.identity)
            observed_status = "simulated" if evidence_category == "simulation" else "observed"
            evidence["identity.system_info"] = CapabilityEvidence(observed_status, dict(identity))
            phase = "battery.state_voltage"
            battery = self.owner.serialized(self.driver.backend.battery)
            evidence["battery.state_voltage"] = CapabilityEvidence(observed_status, dict(battery))
            battery_state = str(battery.get("state", "unknown")).lower()
            battery_blocks_actions = evidence_category != "simulation" and battery_state not in {
                "ok",
                "charged",
                "charging",
                "not_charging",
            }
            for capability in STATIONARY_CAPABILITIES[2:]:
                if battery_blocks_actions:
                    evidence[capability] = CapabilityEvidence(
                        "untested",
                        {"reason": f"battery state {battery_state!r} blocks hardware actions"},
                    )
                    continue
                try:
                    phase = capability

                    def exercise(capability_name: str = capability) -> Mapping[str, object]:
                        return self.driver.backend.exercise_stationary(capability_name)

                    detail = self.owner.serialized(exercise)
                except PermissionError as exc:
                    evidence[capability] = CapabilityEvidence("untested", {"reason": str(exc)})
                else:
                    evidence[capability] = CapabilityEvidence(observed_status, dict(detail))
            for capability in MOVEMENT_CAPABILITIES:
                evidence[capability] = CapabilityEvidence(
                    "untested", {"reason": "requires separately authorized motion HIL"}
                )
            try:
                phase = "stop.latency"
                self.driver.safe_hold()
            except TimeoutError:
                evidence["stop.latency"] = CapabilityEvidence(
                    "failed",
                    {
                        "reason": "stop command acknowledgement timeout",
                        "fail_closed": "BLE disconnected without retry",
                    },
                )
                final_state = "disconnected_stop_unconfirmed"
            else:
                self.owner.mark_ready()
        except Exception as error:
            primary_failure = (phase, error)
        finally:
            try:
                self.owner.disconnect("stationary_probe_complete")
            except Exception as error:
                disconnect_failure = error
        if primary_failure is not None:
            failure_phase, original_failure = primary_failure
            if hasattr(original_failure, "phase"):
                failure_phase = f"{failure_phase}.{original_failure.phase}"
            raise CapabilityProbeError(
                failure_phase,
                getattr(original_failure, "error_type", type(original_failure).__name__),
                cleanup_error_type=(
                    type(disconnect_failure).__name__ if disconnect_failure is not None else None
                ),
            ) from original_failure
        if disconnect_failure is not None:
            raise CapabilityProbeError(
                "disconnect", type(disconnect_failure).__name__
            ) from disconnect_failure
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
            final_state=final_state,
        )
