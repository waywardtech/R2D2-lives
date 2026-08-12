"""Replaceable R2 service seams required from the first scaffold."""

from __future__ import annotations

from typing import Mapping, Protocol


class SpeechToText(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class WakeWordDetector(Protocol):
    def detected(self, audio: bytes) -> bool: ...


class ReasoningDispatcher(Protocol):
    def dispatch(self, text: str, context: Mapping[str, object]) -> Mapping[str, object]: ...


class NotificationSink(Protocol):
    def notify(self, event_type: str, message: str) -> None: ...
