from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from r2_runtime.chat_migrations import upgrade_chat_database
from r2_runtime.conversation import ConversationStore
from r2_runtime.model_conversation import (
    SYSTEM_PROMPT,
    SafeModelConversationDispatcher,
    validate_endpoint,
)


class ModelConversationTest(unittest.TestCase):
    def make_store(self, directory: str) -> tuple[ConversationStore, str]:
        path = Path(directory) / "continuity.sqlite3"
        upgrade_chat_database(path)
        store = ConversationStore(path)
        return store, store.ensure_session(None)

    def test_valid_model_reply_has_no_tools_and_receives_bounded_context(self) -> None:
        captured: dict[str, object] = {}

        def transport(endpoint: str, key: str, body: bytes, timeout: float) -> bytes:
            captured.update(json.loads(body))
            content = json.dumps(
                {"binary": "bweep-brrt · deet!", "translation": "I'm with you. Let's solve it."}
            )
            return json.dumps({"choices": [{"message": {"content": content}}]}).encode()

        with tempfile.TemporaryDirectory() as directory:
            store, session_id = self.make_store(directory)
            store.record(session_id, "Hello", "Hello, pilot.")
            dispatcher = SafeModelConversationDispatcher(
                endpoint="https://models.example/v1/chat/completions",
                model="test-model",
                api_key="secret",
                transport=transport,
            )
            binary, translation, mode = dispatcher.reply_result(
                "What do you think?", session_id, store, {"overall": "nominal"}
            )
            self.assertEqual(mode, "model")
            self.assertTrue(binary.startswith("bweep"))
            self.assertIn("solve", translation)
            self.assertNotIn("tools", captured)
            self.assertIn("English is a console", SYSTEM_PROMPT)
            self.assertLessEqual(len(captured["messages"]), 12)  # type: ignore[arg-type]
            store.close()

    def test_invalid_shape_or_transport_failure_uses_local_fallback(self) -> None:
        def invalid(_endpoint: str, _key: str, _body: bytes, _timeout: float) -> bytes:
            return b'{"choices":[{"message":{"content":"{\\"translation\\":\\"Drive now\\"}"}}]}'

        with tempfile.TemporaryDirectory() as directory:
            store, session_id = self.make_store(directory)
            dispatcher = SafeModelConversationDispatcher(
                endpoint="http://127.0.0.1:11434/v1/chat/completions",
                model="local",
                api_key="local",
                transport=invalid,
            )
            _binary, translation, mode = dispatcher.reply_result(
                "Drive over here", session_id, store, {}
            )
            self.assertEqual(mode, "local-fallback")
            self.assertIn("cannot command movement", translation)
            store.close()

    def test_endpoint_and_output_policy_fail_closed(self) -> None:
        for endpoint in ("http://models.example/v1", "file:///tmp/model", "https://u:p@x.test"):
            with self.assertRaises(ValueError):
                validate_endpoint(endpoint)
