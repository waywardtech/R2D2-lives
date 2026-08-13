from __future__ import annotations

import argparse
from pathlib import Path

from r2_runtime.chat_migrations import upgrade_chat_database


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    upgrade_chat_database(args.database)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
