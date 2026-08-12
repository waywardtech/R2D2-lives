"""Privacy-safe nearby-droid chat planning and stationary expression compilation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import random
from typing import Mapping

from .interfaces import ReasoningDispatcher

SUPPORTED_DROID_KINDS = frozenset({"bb8", "bb9e", "r2d2", "r2q5"})
ALLOWED_SEMANTICS = frozenset({"greeting", "curiosity", "excitement", "uncertain"})

_DEFAULT_SEMANTIC = {
    "bb8": "greeting",
    "bb9e": "uncertain",
    "r2d2": "excitement",
    "r2q5": "curiosity",
}

_AUDIO_PALETTES = {
    "greeting": ("R2_HEY_1", "R2_HEY_3", "R2_CHATTY_1", "R2_POSITIVE_1"),
    "curiosity": ("R2_CHATTY_5", "R2_CHATTY_12", "R2_HEY_7", "R2_POSITIVE_4"),
    "excitement": ("R2_EXCITED_1", "R2_EXCITED_3", "R2_LAUGH_1", "R2_POSITIVE_8"),
    "uncertain": ("R2_CHATTY_9", "R2_CHATTY_20", "R2_HEY_11", "R2_POSITIVE_2"),
}

_HEAD_GESTURES = {
    "greeting": (0.0, -16.0, 16.0, 0.0),
    "curiosity": (0.0, 12.0, -12.0, 0.0),
    "excitement": (0.0, -20.0, 20.0, 0.0),
    "uncertain": (0.0, 8.0, -8.0, 0.0),
}


@dataclass(frozen=True)
class StationaryExpressionPlan:
    semantic: str
    audio_name: str
    head_positions_deg: tuple[float, ...]
    logic_display_brightness: int = 8
    logic_display_pattern: tuple[int, ...] = (0, 8, 0, 8, 0)
    audio_volume: int = 8
    audio_dwell_s: float = 1.25
    light_dwell_s: float = 0.12

    def __post_init__(self) -> None:
        if self.semantic not in ALLOWED_SEMANTICS:
            raise ValueError("unsupported stationary expression semantic")
        if self.audio_name not in _AUDIO_PALETTES[self.semantic]:
            raise ValueError("audio is outside the semantic expression palette")
        if not self.head_positions_deg or self.head_positions_deg[-1] != 0.0:
            raise ValueError("stationary expression must restore the neutral head position")
        if any(abs(position) > 20.0 for position in self.head_positions_deg):
            raise ValueError("stationary expression exceeds the 20 degree head bound")
        if not 0 <= self.logic_display_brightness <= 8:
            raise ValueError("logic-display brightness must be in [0, 8]")
        if not self.logic_display_pattern or self.logic_display_pattern[-1] != 0:
            raise ValueError("stationary expression must finish with logic displays off")
        if any(not 0 <= level <= 8 for level in self.logic_display_pattern):
            raise ValueError("logic-display pattern levels must be in [0, 8]")
        if not 0 <= self.audio_volume <= 8:
            raise ValueError("stationary expression volume must be in [0, 8]")
        if not 0.1 <= self.audio_dwell_s <= 2.0:
            raise ValueError("audio dwell must be in [0.1, 2.0] seconds")
        if not 0.05 <= self.light_dwell_s <= 0.5:
            raise ValueError("light dwell must be in [0.05, 0.5] seconds")


@dataclass(frozen=True)
class DroidEncounterReaction:
    nearby_droid_kind: str
    encounter_count: int
    plan: StationaryExpressionPlan
    reasoning_source: str

    def to_dict(self) -> dict[str, object]:
        return {
            "nearby_droid_kind": self.nearby_droid_kind,
            "encounter_count": self.encounter_count,
            "plan": asdict(self.plan),
            "reasoning_source": self.reasoning_source,
        }


class DroidEncounterChat:
    """Lets chat choose meaning while deterministic code owns physical primitives."""

    def __init__(
        self,
        *,
        dispatcher: ReasoningDispatcher | None = None,
        seed: int = 20260811,
    ) -> None:
        self._dispatcher = dispatcher
        self._seed = seed
        self._last_audio_name: str | None = None

    def plan(self, nearby_droid_kind: str, encounter_count: int) -> DroidEncounterReaction:
        if nearby_droid_kind not in SUPPORTED_DROID_KINDS:
            raise ValueError("unsupported nearby droid kind")
        if encounter_count < 1:
            raise ValueError("encounter count must be positive")

        semantic = _DEFAULT_SEMANTIC[nearby_droid_kind]
        source = "deterministic_fallback"
        if self._dispatcher is not None:
            context: Mapping[str, object] = {
                "event": "nearby_droid_observed",
                "nearby_droid_kind": nearby_droid_kind,
                "encounter_count": encounter_count,
                "motion_allowed": False,
                "allowed_semantics": tuple(sorted(ALLOWED_SEMANTICS)),
            }
            try:
                response = self._dispatcher.dispatch("A nearby droid was noticed.", context)
            except Exception:
                response = {}
            candidate = response.get("semantic_expression")
            if isinstance(candidate, str) and candidate in ALLOWED_SEMANTICS:
                semantic = candidate
                source = "reasoning_dispatcher"

        material = f"{self._seed}:{nearby_droid_kind}:{encounter_count}:{semantic}".encode()
        selection_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
        palette = _AUDIO_PALETTES[semantic]
        audio_name = random.Random(selection_seed).choice(palette)
        if audio_name == self._last_audio_name:
            audio_name = palette[(palette.index(audio_name) + 1) % len(palette)]
        self._last_audio_name = audio_name
        plan = StationaryExpressionPlan(
            semantic=semantic,
            audio_name=audio_name,
            head_positions_deg=_HEAD_GESTURES[semantic],
        )
        return DroidEncounterReaction(nearby_droid_kind, encounter_count, plan, source)


def allowed_audio_names() -> frozenset[str]:
    return frozenset(name for palette in _AUDIO_PALETTES.values() for name in palette)


def proof_of_life_plan(seed: int) -> StationaryExpressionPlan:
    """Compile one reproducibly random, bounded, non-locomotive R2 expression."""

    chooser = random.Random(seed)
    semantic = chooser.choice(tuple(sorted(ALLOWED_SEMANTICS)))
    audio_name = chooser.choice(_AUDIO_PALETTES[semantic])
    return StationaryExpressionPlan(
        semantic=semantic,
        audio_name=audio_name,
        head_positions_deg=_HEAD_GESTURES[semantic],
    )
