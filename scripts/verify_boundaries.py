"""Reject private cross-product imports and direct peer references."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "r2-runtime": (re.compile(r"\b(?:from|import)\s+(?:bat_space_modeler|bsm)\b"),),
    "bat-space-modeler": (re.compile(r"\b(?:from|import)\s+r2_runtime\b"),),
}

violations: list[str] = []
for project, patterns in RULES.items():
    for path in (ROOT / project).rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(text):
                violations.append(f"{path.relative_to(ROOT)}: {pattern.pattern}")

if violations:
    raise SystemExit("cross-product dependency violation:\n" + "\n".join(violations))
print("product boundary check passed")
