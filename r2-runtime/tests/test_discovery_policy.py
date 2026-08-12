from __future__ import annotations

from dataclasses import dataclass
import unittest

from r2_runtime.discovery_policy import select_configured_toy


@dataclass(frozen=True)
class Toy:
    name: str | None


class DiscoveryPolicyTest(unittest.TestCase):
    def test_selects_exact_configured_identity_among_other_r2_advertisements(self) -> None:
        selected = select_configured_toy(
            [Toy("D2-NEARBY"), Toy("D2-CONFIGURED"), Toy("BB-OTHER")],
            "D2-CONFIGURED",
        )
        self.assertEqual(selected.name, "D2-CONFIGURED")

    def test_missing_or_duplicate_exact_identity_fails_closed_without_names(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "advertisements: 0") as absent:
            select_configured_toy([Toy("D2-OTHER")], "D2-PRIVATE")
        self.assertNotIn("D2-PRIVATE", str(absent.exception))
        with self.assertRaisesRegex(RuntimeError, "advertisements: 2") as duplicate:
            select_configured_toy([Toy("D2-PRIVATE"), Toy("D2-PRIVATE")], "D2-PRIVATE")
        self.assertNotIn("D2-PRIVATE", str(duplicate.exception))

    def test_empty_configuration_refuses_before_selection(self) -> None:
        with self.assertRaisesRegex(ValueError, "required before discovery"):
            select_configured_toy([Toy("D2-ANY")], "")


if __name__ == "__main__":
    unittest.main()
