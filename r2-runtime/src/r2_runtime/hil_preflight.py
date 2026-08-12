"""Pure validation for the separately invoked stationary HIL command."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Mapping

PREFLIGHT_FLAGS = (
    "operator_present",
    "device_inspected",
    "temperature_ok",
    "keepout_clear",
    "emergency_stop_ready",
)

STOP_BENCH_FLAGS = PREFLIGHT_FLAGS + (
    "unplugged_from_charger",
    "physically_contained",
    "second_go_confirmed",
)


@dataclass(frozen=True)
class StopBenchPreflight:
    identity: str
    clock_sync_source: str
    clock_uncertainty_ms: float


@dataclass(frozen=True)
class StationaryEncounterPreflight:
    identity: str
    max_reactions: int


@dataclass(frozen=True)
class ProofOfLifePreflight:
    identity: str


def validate_stationary_preflight(args: argparse.Namespace, environment: Mapping[str, str]) -> str:
    if not args.authorize_stationary_hil:
        raise ValueError("HIL disabled: explicit stationary authorization is required")
    missing = [name.replace("_", "-") for name in PREFLIGHT_FLAGS if not getattr(args, name)]
    if missing:
        raise ValueError("HIL disabled: incomplete preflight: " + ", ".join(missing))
    identity = environment.get("R2_DEVICE_IDENTITY", "")
    if not identity:
        raise ValueError("HIL disabled: R2_DEVICE_IDENTITY must be supplied outside source control")
    if args.allow_audio_preview and args.audio_id is None:
        raise ValueError("HIL disabled: audio preview requires an explicit verified --audio-id")
    return identity


def validate_stop_bench_preflight(
    args: argparse.Namespace, environment: Mapping[str, str]
) -> StopBenchPreflight:
    if not args.authorize_stop_response_bench:
        raise ValueError("bench disabled: exact stop-response authorization is required")
    missing = [name.replace("_", "-") for name in STOP_BENCH_FLAGS if not getattr(args, name)]
    if missing:
        raise ValueError("bench disabled: incomplete preflight: " + ", ".join(missing))
    identity = environment.get("R2_DEVICE_IDENTITY", "")
    if not identity:
        raise ValueError("bench disabled: R2_DEVICE_IDENTITY is required outside source control")
    if environment.get("R2_STOP_BENCH_ARM_TOKEN") != "AUTHORIZE_ONE_RAW_MOTOR_OFF":
        raise ValueError("bench disabled: exact external arm token is required")
    sync_source = environment.get("R2_CLOCK_SYNC_SOURCE", "")
    if sync_source not in {"ntp", "chrony"}:
        raise ValueError("bench disabled: synchronized R2_CLOCK_SYNC_SOURCE is required")
    try:
        uncertainty_ms = float(environment.get("R2_CLOCK_UNCERTAINTY_MS", ""))
    except ValueError as exc:
        raise ValueError("bench disabled: valid clock uncertainty is required") from exc
    if not 0 <= uncertainty_ms <= 1000:
        raise ValueError("bench disabled: clock uncertainty must be in [0, 1000] ms")
    return StopBenchPreflight(identity, sync_source, uncertainty_ms)


def validate_stationary_encounter_preflight(
    args: argparse.Namespace, environment: Mapping[str, str]
) -> StationaryEncounterPreflight:
    if not args.authorize_stationary_encounter:
        raise ValueError("encounter HIL disabled: exact stationary authorization is required")
    required = PREFLIGHT_FLAGS + ("charging_safe_only", "second_go_confirmed")
    missing = [name.replace("_", "-") for name in required if not getattr(args, name)]
    if missing:
        raise ValueError("encounter HIL disabled: incomplete preflight: " + ", ".join(missing))
    identity = environment.get("R2_DEVICE_IDENTITY", "")
    if not identity:
        raise ValueError(
            "encounter HIL disabled: R2_DEVICE_IDENTITY is required outside source control"
        )
    if environment.get("R2_ENCOUNTER_ARM_TOKEN") != "AUTHORIZE_STATIONARY_HEAD_AUDIO":
        raise ValueError("encounter HIL disabled: exact external arm token is required")
    if not 1 <= args.max_reactions <= 5:
        raise ValueError("encounter HIL disabled: max reactions must be in [1, 5]")
    return StationaryEncounterPreflight(identity, args.max_reactions)


def validate_proof_of_life_preflight(
    args: argparse.Namespace, environment: Mapping[str, str]
) -> ProofOfLifePreflight:
    if not args.authorize_proof_of_life:
        raise ValueError("proof of life disabled: exact stationary authorization is required")
    required = PREFLIGHT_FLAGS + ("charging_safe_only", "second_go_confirmed")
    missing = [name.replace("_", "-") for name in required if not getattr(args, name)]
    if missing:
        raise ValueError("proof of life disabled: incomplete preflight: " + ", ".join(missing))
    identity = environment.get("R2_DEVICE_IDENTITY", "")
    if not identity:
        raise ValueError(
            "proof of life disabled: R2_DEVICE_IDENTITY is required outside source control"
        )
    if environment.get("R2_PROOF_OF_LIFE_ARM_TOKEN") != "AUTHORIZE_STATIONARY_PROOF_OF_LIFE":
        raise ValueError("proof of life disabled: exact external arm token is required")
    return ProofOfLifePreflight(identity)
