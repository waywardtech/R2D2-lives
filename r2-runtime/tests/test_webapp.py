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
        for forbidden in ("/drive", "/move", "/heading", "/proof-of-life"):
            self.assertNotIn(forbidden, javascript)

    def test_manifest_is_scoped_to_r2d2_and_status_is_not_service_worker_cached(self) -> None:
        manifest = json.loads((WEBAPP / "manifest.webmanifest").read_text(encoding="utf-8"))
        worker = (WEBAPP / "service-worker.js").read_text(encoding="utf-8")
        self.assertEqual(manifest["start_url"], "/R2D2/")
        self.assertEqual(manifest["scope"], "/R2D2/")
        self.assertIn('endsWith("/status.json")', worker)
        self.assertNotIn('"status.json"', worker.split("const STATIC", 1)[1].split(";", 1)[0])

    def test_apache_surface_is_lan_only_read_only_and_hardened(self) -> None:
        config = (ROOT / "r2-runtime" / "deploy" / "apache" / "r2d2-dashboard.conf").read_text(
            encoding="utf-8"
        )
        self.assertIn('Alias "/R2D2/"', config)
        self.assertIn("RedirectMatch 302 ^/R2D2$ /R2D2/", config)
        self.assertIn("Require ip", config)
        self.assertIn("Content-Security-Policy", config)
        self.assertNotIn("ProxyPass", config)


if __name__ == "__main__":
    unittest.main()
