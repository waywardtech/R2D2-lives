"""Validated, privacy-safe capability profile for an observed R201 firmware."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CapabilityState = Literal["verified", "failed", "unsupported", "untested", "unverified"]


class CapabilityEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: CapabilityState
    claim: str = Field(min_length=1, max_length=240)
    evidence: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_evidence_for_terminal_claims(self) -> "CapabilityEntry":
        if self.state in {"verified", "failed", "unsupported"} and not self.evidence:
            raise ValueError(f"{self.state} capability requires evidence")
        return self


class FirmwareCapabilityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    model: Literal["R2-D2 R201"]
    firmware: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    library_baseline: Literal["0.12.1"]
    device_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    generated_at: str
    capabilities: dict[str, CapabilityEntry]
    gate_p1_complete: bool

    @model_validator(mode="after")
    def require_gate_inventory(self) -> "FirmwareCapabilityProfile":
        required = {
            "ble.connect_disconnect",
            "battery.state_voltage",
            "wake.stance_cycle",
            "led.dome_logic_display",
            "head.position_read",
            "audio.quiet_preview",
            "stop.command_acknowledgement",
            "stop.physical_effectiveness",
            "drive.bounded_calibration",
            "emergency_stop.physical",
        }
        missing = required - self.capabilities.keys()
        if missing:
            raise ValueError(f"capability profile missing gate entries: {sorted(missing)}")
        physical_gates = (
            "stop.physical_effectiveness",
            "drive.bounded_calibration",
            "emergency_stop.physical",
        )
        if self.gate_p1_complete and any(
            self.capabilities[name].state != "verified" for name in physical_gates
        ):
            raise ValueError(
                "Gate P1 cannot complete before every physical motion gate is verified"
            )
        return self


def load_capability_profile(path: Path) -> FirmwareCapabilityProfile:
    return FirmwareCapabilityProfile.model_validate_json(path.read_text(encoding="utf-8"))


def profile_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_profile_json(profile: FirmwareCapabilityProfile) -> str:
    return json.dumps(profile.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
