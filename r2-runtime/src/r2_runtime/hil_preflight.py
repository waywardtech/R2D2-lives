"""Pure validation for the separately invoked stationary HIL command."""

from __future__ import annotations

import argparse
from typing import Mapping

PREFLIGHT_FLAGS = (
    "operator_present",
    "device_inspected",
    "temperature_ok",
    "keepout_clear",
    "emergency_stop_ready",
)


def validate_stationary_preflight(
    args: argparse.Namespace, environment: Mapping[str, str]
) -> str:
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

