"""Alembic migration entry point for the isolated chat continuity database."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_chat_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).with_name("migrations")))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path.as_posix()}")
    command.upgrade(config, "head")
