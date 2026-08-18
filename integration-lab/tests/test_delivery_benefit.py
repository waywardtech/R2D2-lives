from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "verify_delivery_benefit", ROOT / "scripts" / "verify_delivery_benefit.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DeliveryBenefitTest(unittest.TestCase):
    def test_committed_register_is_valid(self) -> None:
        payload = json.loads((ROOT / "planning" / "benefit-register.json").read_text())
        MODULE.validate_register(payload)

    def test_completed_entry_requires_a_measured_result(self) -> None:
        payload = {
            "schema_version": "1.0",
            "policy": "Build only with measurable benefit.",
            "entries": [
                {
                    "id": "example",
                    "scope": "simulation",
                    "state": "completed_no_benefit",
                    "hypothesis": "Example",
                    "baseline": {"evidence": []},
                    "measurement": {
                        "metric": "value",
                        "unit": "count",
                        "threshold": "> 0",
                        "collection": "test",
                    },
                    "decision_rule": "test",
                    "sources": [{"kind": "official", "url": "https://example.test"}],
                    "next_action": "stop",
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "require a result"):
            MODULE.validate_register(payload)


if __name__ == "__main__":
    unittest.main()
