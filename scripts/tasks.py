"""Stable, dependency-free Phase 0 task entry points."""

from __future__ import annotations

import argparse
import compileall
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROJECT_SOURCES = (
    ROOT / "protocol" / "src",
    ROOT / "r2-runtime" / "src",
    ROOT / "bat-space-modeler" / "src",
)


def _pythonpath(*paths: Path) -> str:
    existing = os.environ.get("PYTHONPATH", "")
    values = [str(path) for path in paths]
    if existing:
        values.append(existing)
    return os.pathsep.join(values)


def _run(command: list[str], *, paths: tuple[Path, ...] = PROJECT_SOURCES) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = _pythonpath(*paths)
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def bootstrap() -> None:
    if sys.version_info[:2] != (3, 11):
        raise SystemExit("Phase 0 requires Python 3.11")
    print("Python 3.11 available; Phase 0 has no third-party runtime dependencies.")


def check() -> None:
    ok = compileall.compile_dir(ROOT / "protocol", quiet=1)
    ok &= compileall.compile_dir(ROOT / "r2-runtime", quiet=1)
    ok &= compileall.compile_dir(ROOT / "bat-space-modeler", quiet=1)
    if not ok:
        raise SystemExit("byte-compilation failed")
    _run([sys.executable, "protocol/tools/generate_clients.py", "--check"])
    _run([sys.executable, "scripts/verify_boundaries.py"])
    _run([sys.executable, "scripts/verify_standalone.py"])


def contract() -> None:
    _run([sys.executable, "-m", "unittest", "discover", "-s", "protocol/tests", "-v"], paths=(PROJECT_SOURCES[0],))


def sim_smoke() -> None:
    _run([sys.executable, "integration-lab/sim_roundtrip.py"])


def p1_sim() -> None:
    _run([sys.executable, "integration-lab/p1_stationary_probe.py"])


def test() -> None:
    check()
    contract()
    for project in ("r2-runtime", "bat-space-modeler", "integration-lab"):
        _run([sys.executable, "-m", "unittest", "discover", "-s", f"{project}/tests", "-v"])


def docs_check() -> None:
    required = [
        ROOT / "AGENTS.md",
        ROOT / "STATUS.md",
        ROOT / "CHANGELOG.md",
        ROOT / "docs" / "phase-0-operator.md",
        ROOT / "docs" / "phase-1-stationary-probe.md",
        ROOT / "docs" / "r201-stop-response-bench.md",
        ROOT / "r2-runtime" / "hardware-provenance.toml",
        ROOT / "r2-runtime" / "requirements-hardware-pi.lock",
        ROOT / "r2-runtime" / "hardware-wheelhouse.manifest.json",
        ROOT / "r2-runtime" / "THIRD_PARTY_NOTICES.md",
        ROOT / "traceability" / "evidence.csv",
        ROOT / "evidence" / "hil" / "cycle-1-stop-timeout.json",
        ROOT / "evidence" / "hil" / "cycle-1-stop-timeout.json.sha256",
        ROOT / "specs" / "traceability" / "requirements.csv",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"missing required documentation: {missing}")
    status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    for phrase in ("Phase 0", "Simulation", "Real R2 movement authorized for next run: no"):
        if phrase not in status:
            raise SystemExit(f"STATUS.md missing required phrase: {phrase}")
    json.loads((ROOT / "protocol" / "schema" / "sap-common.schema.json").read_text(encoding="utf-8"))
    hil_evidence = ROOT / "evidence" / "hil" / "cycle-1-stop-timeout.json"
    expected_hil_hash = (
        (ROOT / "evidence" / "hil" / "cycle-1-stop-timeout.json.sha256")
        .read_text(encoding="utf-8")
        .split()[0]
    )
    if hashlib.sha256(hil_evidence.read_bytes()).hexdigest() != expected_hil_hash:
        raise SystemExit("HIL evidence hash mismatch")
    _run([sys.executable, "scripts/verify_hardware_lock.py"])
    yaml_expectations = {
        "agent-api.openapi.yaml": ("openapi: 3.1.0", "paths:", "SAP-Version"),
        "spatial-provider-api.openapi.yaml": ("openapi: 3.1.0", "paths:", "sap-common.schema.json"),
        "events.asyncapi.yaml": ("asyncapi:", "channels:", "sap-common.schema.json"),
    }
    for name, markers in yaml_expectations.items():
        text = (ROOT / "protocol" / "schema" / name).read_text(encoding="utf-8")
        if "\t" in text or any(marker not in text for marker in markers):
            raise SystemExit(f"contract structure check failed: {name}")
    print("documentation and JSON schema checks passed")


TASKS = {
    "bootstrap": bootstrap,
    "check": check,
    "contract": contract,
    "sim-smoke": sim_smoke,
    "p1-sim": p1_sim,
    "test": test,
    "docs-check": docs_check,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=TASKS)
    args = parser.parse_args()
    TASKS[args.task]()


if __name__ == "__main__":
    main()
