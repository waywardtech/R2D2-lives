"""Offline scan of tracked files for secret/device data and license coverage."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_NAMES = {".env", "credentials.json", "id_rsa", "id_ed25519"}
SECRET_PATTERNS = {
    "private key": re.compile("-----BEGIN " + "PRIVATE KEY-----"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "OpenAI key": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "BLE MAC address": re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])"),
    "R2 advertised identity": re.compile(r"\bD2-[0-9A-F]{4}\b"),
    "BB advertised identity": re.compile(r"\bBB-[0-9A-F]{4}\b"),
}


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return [ROOT / value.decode() for value in result.stdout.split(b"\0") if value]


def _verify_tracked_text() -> None:
    failures: list[str] = []
    for path in _tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            failures.append(f"forbidden credential filename: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{label} pattern in {relative}")
    if failures:
        raise SystemExit("repository hygiene check failed: " + "; ".join(failures))


def _verify_dependency_notices() -> None:
    manifest = json.loads(
        (ROOT / "r2-runtime" / "hardware-wheelhouse.manifest.json").read_text(encoding="utf-8")
    )
    notices = (ROOT / "r2-runtime" / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8").lower()
    missing = [
        package for package in manifest["required_packages"] if package.lower() not in notices
    ]
    if missing:
        raise SystemExit(f"third-party notices missing locked packages: {missing}")
    for required in ("license:", "redistributions must include", "not vendored"):
        if required not in notices:
            raise SystemExit(f"third-party notices missing policy text: {required}")


def main() -> None:
    _verify_tracked_text()
    _verify_dependency_notices()
    print("tracked secret/device patterns and dependency notices verified")


if __name__ == "__main__":
    main()
