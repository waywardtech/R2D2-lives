"""Reject hosted-CI workflows that could reach hardware or external identities."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED = (
    "runs-on: ubuntu-latest",
    "uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6",
    "uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6",
    'python-version: "3.11"',
    "python scripts/tasks.py test",
    "python scripts/tasks.py p1-sim",
    "python scripts/tasks.py proof-of-life-sim",
    "python scripts/verify_repository_hygiene.py",
    "permissions:\n  contents: read",
)
BANNED = (
    "self-hosted",
    "hil_",
    "bluetoothctl",
    "R2_DEVICE_IDENTITY",
    "R2_STOP_BENCH_ARM_TOKEN",
    "ssh ",
    "scp ",
    "sudo ",
    "cache: pip",
    "uses: actions/checkout@v",
    "uses: actions/setup-python@v",
    "secrets.",
)


def main() -> None:
    if not WORKFLOW.is_file():
        raise SystemExit("missing simulation CI workflow")
    text = WORKFLOW.read_text(encoding="utf-8")
    missing = [value for value in REQUIRED if value not in text]
    forbidden = [value for value in BANNED if value.lower() in text.lower()]
    if missing:
        raise SystemExit(f"CI workflow missing safety requirement: {missing}")
    if forbidden:
        raise SystemExit(f"CI workflow contains hardware-capable token: {forbidden}")
    print("hosted CI is simulation-only")


if __name__ == "__main__":
    main()
