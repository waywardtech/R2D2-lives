"""Privacy-safe exact-identity selection for live droid discovery."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TypeVar


class AdvertisedToy(Protocol):
    name: str | None


ToyT = TypeVar("ToyT", bound=AdvertisedToy)


def select_configured_toy(toys: Iterable[ToyT], configured_identity: str) -> ToyT:
    """Select one exact configured identity without exposing nearby identities."""
    if not configured_identity:
        raise ValueError("configured droid identity is required before discovery")
    matches = [toy for toy in toys if toy.name == configured_identity]
    if len(matches) != 1:
        raise RuntimeError(
            f"configured R2 identity matches observed advertisements: {len(matches)}"
        )
    return matches[0]
