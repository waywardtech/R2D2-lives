from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.routing import APIRoute

from r2_runtime.chat_api import ChatRequest, ChatResponse, create_app


class ChatApiTest(unittest.TestCase):
    def test_chat_route_is_bounded_and_non_actuating(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = {
                "R2_CHAT_DATABASE": str(root / "continuity.sqlite3"),
                "R2_STATUS_PATH": str(root / "missing-status.json"),
            }
            with patch.dict(os.environ, environment):
                app = create_app()
            routes = {route.path: route for route in app.routes if isinstance(route, APIRoute)}
            self.assertEqual(set(routes), {"/health", "/chat"})
            response = routes["/chat"].endpoint(ChatRequest(message="Hello R2"))
            self.assertIsInstance(response, ChatResponse)
            self.assertFalse(response.physical_action)
            self.assertEqual(response.mode, "local")
            self.assertEqual(len(response.session_id), 32)
            app.state.conversation_store.close()

    def test_boundary_model_rejects_extra_fields_and_long_messages(self) -> None:
        with self.assertRaises(ValueError):
            ChatRequest.model_validate({"message": "hello", "motor": "drive"})
        with self.assertRaises(ValueError):
            ChatRequest(message="x" * 281)

    def test_partial_model_configuration_fails_startup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = {
                "R2_CHAT_DATABASE": str(Path(directory) / "continuity.sqlite3"),
                "R2_CHAT_MODEL_ENDPOINT": "https://models.example/v1/chat/completions",
                "R2_CHAT_MODEL": "",
                "R2_CHAT_API_KEY_FILE": "",
            }
            with patch.dict(os.environ, environment, clear=True), self.assertRaises(RuntimeError):
                create_app()
