from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from r2_runtime.conversation import (
    MAX_TURNS,
    ConversationStore,
    LocalConversationDispatcher,
    validate_message,
)
from r2_runtime.chat_migrations import upgrade_chat_database


class ConversationTest(unittest.TestCase):
    def make_store(self, directory: str) -> ConversationStore:
        path = Path(directory) / "continuity.sqlite3"
        upgrade_chat_database(path)
        return ConversationStore(path)

    def test_session_remembers_name_and_refuses_physical_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self.make_store(directory)
            dispatcher = LocalConversationDispatcher()
            session_id = store.ensure_session(None)
            binary, reply = dispatcher.reply("Call me Luke", session_id, store, {})
            store.record(session_id, "Call me Luke", reply)
            self.assertTrue(binary)
            self.assertIn("Luke", reply)
            _, recalled = dispatcher.reply("What is my name?", session_id, store, {})
            self.assertIn("Luke", recalled)
            _, refusal = dispatcher.reply("Drive over here", session_id, store, {})
            self.assertIn("cannot command movement", refusal)
            vocalization, threepio = dispatcher.reply("Tell me about C-3PO", session_id, store, {})
            self.assertRegex(vocalization, r"^[a-z!?. ·-]+$")
            self.assertIn("oldest friend", threepio)
            self.assertNotIn("I said", vocalization)
            store.close()

    def test_invalid_session_is_replaced_and_turns_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self.make_store(directory)
            session_id = store.ensure_session("not-a-session")
            self.assertEqual(len(session_id), 32)
            for number in range(MAX_TURNS + 3):
                store.record(session_id, f"user {number}", f"reply {number}")
            self.assertEqual(store.turn_count(session_id), MAX_TURNS)
            history = store.recent_history(session_id, limit=2)
            self.assertEqual(len(history), 4)
            self.assertEqual([item["role"] for item in history], ["user", "assistant"] * 2)
            store.close()

    def test_messages_are_printable_and_bounded(self) -> None:
        self.assertEqual(validate_message(" hello "), "hello")
        for bad in ("", "x" * 281, "unsafe\x00text"):
            with self.assertRaises(ValueError):
                validate_message(bad)

    def test_local_personality_and_contextual_repair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self.make_store(directory)
            dispatcher = LocalConversationDispatcher()
            session_id = store.ensure_session(None)
            _, identity = dispatcher.reply("Who are you?", session_id, store, {})
            self.assertIn("R2-D2", identity)
            store.record(session_id, "Who are you?", identity)
            _, recalled = dispatcher.reply("What did I say?", session_id, store, {})
            self.assertIn("Who are you?", recalled)
            _, thanks = dispatcher.reply("Thank you", session_id, store, {})
            self.assertIn("operation", thanks)
            _, clarification = dispatcher.reply("yes", session_id, store, {})
            self.assertIn("detail", clarification)
            store.close()

    def test_status_issues_are_bounded_and_movement_substrings_do_not_false_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self.make_store(directory)
            dispatcher = LocalConversationDispatcher()
            session_id = store.ensure_session(None)
            issues = [{"summary": f"issue {number}"} for number in range(5)]
            _, reply = dispatcher.reply("Any problems?", session_id, store, {"issues": issues})
            self.assertIn("5 reported", reply)
            self.assertIn("issue 2", reply)
            self.assertNotIn("issue 3", reply)
            _, conversation = dispatcher.reply("This is a moving story", session_id, store, {})
            self.assertNotIn("cannot command movement", conversation)
            store.close()
