from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class R2Config:
    spatial_provider: str = "null"
    droid_driver: str = "sim"

    @classmethod
    def from_env(cls) -> "R2Config":
        config = cls(
            spatial_provider=os.getenv("R2_SPATIAL_PROVIDER", "null"),
            droid_driver=os.getenv("R2_DROID_DRIVER", "sim"),
        )
        if config.spatial_provider not in {"null", "sim"}:
            raise ValueError("R2_SPATIAL_PROVIDER must be null or sim in Phase 0")
        if config.droid_driver != "sim":
            raise ValueError("Phase 0 permits only the simulation droid driver")
        return config
