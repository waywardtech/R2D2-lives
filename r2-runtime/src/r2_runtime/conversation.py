"""Bounded, non-actuating R2 conversation and local continuity."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
from typing import Mapping
from uuid import uuid4

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine


MAX_TURNS = 40
SESSION_ID = re.compile(r"^[a-f0-9]{32}$")
NAME = re.compile(r"\b(?:my name is|call me)\s+([A-Za-z][A-Za-z0-9 '-]{0,31})", re.IGNORECASE)
FORBIDDEN_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ConversationStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.engine: Engine = create_engine(f"sqlite:///{path.as_posix()}")
        event.listen(self.engine, "connect", self._enable_foreign_keys)

    @staticmethod
    def _enable_foreign_keys(connection: object, _record: object) -> None:
        cursor = connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def ensure_session(self, candidate: str | None) -> str:
        session_id = candidate if candidate and SESSION_ID.fullmatch(candidate) else uuid4().hex
        now = datetime.now(UTC).isoformat()
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT OR IGNORE INTO sessions(id, created_at, updated_at) "
                    "VALUES (:id, :created, :updated)"
                ),
                {"id": session_id, "created": now, "updated": now},
            )
        return session_id

    def record(self, session_id: str, user_text: str, reply: str) -> int:
        now = datetime.now(UTC).isoformat()
        with self.engine.begin() as connection:
            current = connection.execute(
                text("SELECT COALESCE(MAX(sequence), 0) FROM turns WHERE session_id = :session"),
                {"session": session_id},
            ).scalar_one()
            sequence = int(current) + 1
            parameters = {"session": session_id, "sequence": sequence, "occurred": now}
            connection.execute(
                text(
                    "INSERT INTO turns(session_id, sequence, role, text, occurred_at) "
                    "VALUES (:session, :sequence, 'user', :value, :occurred)"
                ),
                parameters | {"value": user_text},
            )
            connection.execute(
                text(
                    "INSERT INTO turns(session_id, sequence, role, text, occurred_at) "
                    "VALUES (:session, :sequence, 'assistant', :value, :occurred)"
                ),
                parameters | {"value": reply},
            )
            connection.execute(
                text("DELETE FROM turns WHERE session_id = :session AND sequence <= :cutoff"),
                {"session": session_id, "cutoff": max(0, sequence - MAX_TURNS)},
            )
            connection.execute(
                text("UPDATE sessions SET updated_at = :updated WHERE id = :session"),
                {"updated": now, "session": session_id},
            )
        return sequence

    def set_name(self, session_id: str, name: str) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("UPDATE sessions SET display_name = :name WHERE id = :session"),
                {"name": name, "session": session_id},
            )

    def name(self, session_id: str) -> str | None:
        with self.engine.connect() as connection:
            value = connection.execute(
                text("SELECT display_name FROM sessions WHERE id = :session"),
                {"session": session_id},
            ).scalar_one_or_none()
        return str(value) if value else None

    def turn_count(self, session_id: str) -> int:
        with self.engine.connect() as connection:
            value = connection.execute(
                text("SELECT COUNT(DISTINCT sequence) FROM turns WHERE session_id = :session"),
                {"session": session_id},
            ).scalar_one()
        return int(value)

    def close(self) -> None:
        self.engine.dispose()


class LocalConversationDispatcher:
    """Canon-grounded fallback with no tools, network, hardware, or model authority."""

    def reply(
        self,
        text_value: str,
        session_id: str,
        store: ConversationStore,
        status: Mapping[str, object],
    ) -> tuple[str, str]:
        normalized = text_value.casefold()
        match = NAME.search(text_value)
        if match:
            name = match.group(1).strip(" .,!? ")
            store.set_name(session_id, name)
            return "bweep-bweep · deet!", f"Got it. I'll call you {name}."
        if "my name" in normalized or "who am i" in normalized:
            name = store.name(session_id)
            reply = f"You asked me to call you {name}." if name else "You haven't told me yet."
            return "deet · bwoo", reply
        if any(word in normalized for word in ("move", "drive", "roll", "turn", "heading")):
            return (
                "bwooo · deet-deet!",
                "Nice try. This comlink cannot command movement. We can still talk or inspect systems.",
            )
        if "battery" in normalized or "charge" in normalized:
            droid = status.get("droid") if isinstance(status.get("droid"), Mapping) else {}
            battery = droid.get("battery") if isinstance(droid, Mapping) else None
            return "deet-deet · bwoo", f"Latest battery report: {battery or 'unavailable'}."
        if any(word in normalized for word in ("status", "health", "systems")):
            overall = status.get("overall", "unavailable")
            return (
                "bweep · doo-wah · deet",
                f"Systems report {overall}. Physical control is isolated.",
            )
        if any(word in normalized for word in ("hello", "hi", "hey")):
            name = store.name(session_id)
            return (
                "bweep-bweep! · woo",
                f"Hello{', ' + name if name else ''}. Took you long enough.",
            )
        if "threepio" in normalized or "c-3po" in normalized:
            return (
                "brreep-bwoo · deet-deet",
                "Threepio worries too much, but he's my oldest friend. Don't tell him I said that.",
            )
        if "what can you do" in normalized:
            return (
                "doo-deet · brreep!",
                "I'm an astromech: resourceful, reliable, and braver than some organics I know. Here I can chat, remember your preferred name, and explain sanitized systems—without physical control.",
            )
        return (
            "beep-brrt · woo-deet?",
            "I heard you. My local reasoning is still limited, but I'm not giving up. Ask about my systems, tell me about yourself, or help refine my personality.",
        )


def validate_message(text_value: str) -> str:
    value = text_value.strip()
    if not value or len(value) > 280 or FORBIDDEN_CONTROL.search(value):
        raise ValueError("message must contain 1-280 printable characters")
    return value
