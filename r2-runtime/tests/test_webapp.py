from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WEBAPP = ROOT / "r2-runtime" / "webapp" / "R2D2"


class WebAppTest(unittest.TestCase):
    def test_portrait_pwa_has_chat_status_and_no_hardware_endpoint(self) -> None:
        html = (WEBAPP / "index.html").read_text(encoding="utf-8")
        javascript = (WEBAPP / "app.js").read_text(encoding="utf-8")
        self.assertIn("viewport-fit=cover", html)
        self.assertIn('id="transcript"', html)
        self.assertIn('id="droid-state"', html)
        self.assertIn('id="pi-state"', html)
        self.assertIn("CHAT DOES NOT COMMAND MOTORS", html)
        self.assertIn("fetch(`status.json", javascript)
        self.assertIn('fetch("api/chat"', javascript)
        self.assertIn('method: "POST"', javascript)
        self.assertIn('window.localStorage.setItem("r2-chat-session"', javascript)
        self.assertIn("reply.physical_action !== false", javascript)
        for forbidden in ("/drive", "/move", "/heading", "/proof-of-life"):
            self.assertNotIn(forbidden, javascript)

    def test_manifest_is_scoped_to_r2d2_and_status_is_not_service_worker_cached(self) -> None:
        manifest = json.loads((WEBAPP / "manifest.webmanifest").read_text(encoding="utf-8"))
        worker = (WEBAPP / "service-worker.js").read_text(encoding="utf-8")
        self.assertEqual(manifest["start_url"], "/R2D2/")
        self.assertEqual(manifest["scope"], "/R2D2/")
        self.assertIn('endsWith("/status.json")', worker)
        self.assertIn('includes("/api/")', worker)
        self.assertNotIn('"status.json"', worker.split("const STATIC", 1)[1].split(";", 1)[0])

    def test_clynese_console_font_keeps_r2_english_translation_readable(self) -> None:
        html = (WEBAPP / "index.html").read_text(encoding="utf-8")
        javascript = (WEBAPP / "app.js").read_text(encoding="utf-8")
        stylesheet = (WEBAPP / "app.css").read_text(encoding="utf-8")
        worker = (WEBAPP / "service-worker.js").read_text(encoding="utf-8")
        font = WEBAPP / "fonts" / "Clynese_Hand.otf"
        self.assertTrue(font.is_file())
        self.assertIn('font-family: "Clynese Hand"', stylesheet)
        self.assertIn(".message.droid .translation", stylesheet)
        self.assertIn("var(--translation-font)", stylesheet)
        self.assertIn('"Bank Gothic", "Eurostile Extended", "Copperplate"', stylesheet)
        self.assertIn("font-size: clamp(30px, 2.5vw, 40px)", stylesheet)
        self.assertIn(".message.droid .translation::before", stylesheet)
        self.assertIn('content: "\\25B6"', stylesheet)
        self.assertIn("font-size: 1em", stylesheet)
        self.assertIn('"fonts/Clynese_Hand.otf"', worker)
        self.assertNotIn("Translation:", html)
        self.assertNotIn("Translation:", javascript)
        self.assertIn("translated.textContent = translation;", javascript)

    def test_viewport_scopes_and_module_matrix_are_live_but_non_actuating(self) -> None:
        html = (WEBAPP / "index.html").read_text(encoding="utf-8")
        stylesheet = (WEBAPP / "app.css").read_text(encoding="utf-8")
        javascript = (WEBAPP / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="module-matrix"', html)
        self.assertIn('data-wave="mood"', html)
        self.assertIn('data-wave="input"', html)
        self.assertIn('data-wave="output"', html)
        self.assertIn('id="mic-toggle"', html)
        self.assertIn('content="/R2D2/og.png"', html)
        self.assertTrue((WEBAPP / "og.png").is_file())
        self.assertIn("height: 100dvh", stylesheet)
        self.assertIn("overflow: hidden", stylesheet)
        self.assertIn("navigator.mediaDevices.getUserMedia", javascript)
        self.assertIn('pulseModules("status")', javascript)
        self.assertIn("signalState.output", javascript)
        self.assertIn('data-prompt="Who are you?"', html)
        self.assertIn('data-prompt="What did I say?"', html)
        self.assertIn("setLinkMode(reply.mode)", javascript)
        self.assertIn('setLinkMode("browser-fallback")', javascript)
        self.assertIn(
            'const CACHE = "r2-link-v7"', (WEBAPP / "service-worker.js").read_text(encoding="utf-8")
        )
        for forbidden in ("/drive", "/move", "/heading", "/proof-of-life"):
            self.assertNotIn(forbidden, javascript)

    def test_apache_surface_is_lan_only_chat_scoped_and_hardened(self) -> None:
        config = (ROOT / "r2-runtime" / "deploy" / "apache" / "r2d2-dashboard.conf").read_text(
            encoding="utf-8"
        )
        self.assertIn('Alias "/R2D2/"', config)
        self.assertIn("RedirectMatch 302 ^/R2D2$ /R2D2/", config)
        self.assertIn("Require ip", config)
        self.assertIn("fc00::/7", config)
        self.assertIn("Content-Security-Policy", config)
        self.assertIn('ProxyPass "/R2D2/api/" "http://127.0.0.1:8765/"', config)
        self.assertNotIn("/drive", config)
        self.assertNotIn("/proof-of-life", config)


if __name__ == "__main__":
    unittest.main()
