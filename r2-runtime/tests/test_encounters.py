from __future__ import annotations

import unittest

from r2_runtime.encounters import (
    DroidEncounterChat,
    StationaryExpressionPlan,
    proof_of_life_plan,
)


class FakeDispatcher:
    def __init__(self, response: object = "curiosity", *, fail: bool = False) -> None:
        self.response = response
        self.fail = fail
        self.context: dict[str, object] = {}

    def dispatch(self, text: str, context: dict[str, object]) -> dict[str, object]:
        if self.fail:
            raise RuntimeError("injected model outage")
        self.context = dict(context)
        return {"semantic_expression": self.response}


class DroidEncounterChatTest(unittest.TestCase):
    def test_seeded_reaction_is_deterministic_and_stationary(self) -> None:
        first = DroidEncounterChat(seed=42).plan("bb8", 1)
        second = DroidEncounterChat(seed=42).plan("bb8", 1)
        self.assertEqual(first, second)
        self.assertEqual(first.plan.head_positions_deg[-1], 0.0)
        self.assertLessEqual(max(map(abs, first.plan.head_positions_deg)), 20.0)
        self.assertTrue(first.plan.audio_name.startswith("R2_"))
        self.assertNotIn("address", str(first.to_dict()).lower())

    def test_consecutive_reactions_do_not_repeat_audio(self) -> None:
        chat = DroidEncounterChat(seed=20260811)
        names = [chat.plan("bb8", count).plan.audio_name for count in range(1, 5)]
        self.assertTrue(all(left != right for left, right in zip(names, names[1:])))

    def test_chat_selects_meaning_but_cannot_select_primitives(self) -> None:
        dispatcher = FakeDispatcher()
        reaction = DroidEncounterChat(dispatcher=dispatcher, seed=7).plan("r2q5", 2)
        self.assertEqual(reaction.plan.semantic, "curiosity")
        self.assertEqual(reaction.reasoning_source, "reasoning_dispatcher")
        self.assertFalse(dispatcher.context["motion_allowed"])
        self.assertNotIn("audio", dispatcher.context)
        self.assertNotIn("head", dispatcher.context)

    def test_invalid_or_failed_chat_falls_back_safely(self) -> None:
        for dispatcher in (FakeDispatcher("drive"), FakeDispatcher(fail=True)):
            with self.subTest(dispatcher=dispatcher):
                reaction = DroidEncounterChat(dispatcher=dispatcher).plan("bb9e", 1)
                self.assertEqual(reaction.plan.semantic, "uncertain")
                self.assertEqual(reaction.reasoning_source, "deterministic_fallback")

    def test_plan_rejects_non_neutral_or_out_of_bounds_head(self) -> None:
        with self.assertRaisesRegex(ValueError, "restore"):
            StationaryExpressionPlan("greeting", "R2_HEY_1", (0.0, 5.0))
        with self.assertRaisesRegex(ValueError, "20 degree"):
            StationaryExpressionPlan("greeting", "R2_HEY_1", (0.0, 21.0, 0.0))

    def test_unknown_droid_kind_is_not_inferred(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported nearby droid"):
            DroidEncounterChat().plan("unknown", 1)

    def test_proof_of_life_plan_is_seeded_bounded_and_restoring(self) -> None:
        first = proof_of_life_plan(42)
        second = proof_of_life_plan(42)
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(set(first.logic_display_pattern)), 2)
        self.assertEqual(first.logic_display_pattern[-1], 0)
        self.assertIn(-abs(first.head_positions_deg[1]), first.head_positions_deg)
        self.assertEqual(first.head_positions_deg[-1], 0.0)
        self.assertEqual(first.audio_volume, 255)
        self.assertEqual(first.audio_dwell_s, 3.5)


if __name__ == "__main__":
    unittest.main()
