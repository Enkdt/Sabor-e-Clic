# OBS-001: health/readiness e correlação por request id.
# Rodar: .venv/bin/python -m unittest tests.test_observability

import logging
import tempfile
import unittest

from app import create_app

logging.disable(logging.CRITICAL)


def _make_app():
    _, path = tempfile.mkstemp(suffix=".db")
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "RATELIMIT_ENABLED": False,
    })


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_health_is_ok_without_db(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_ready_checks_db(self):
        r = self.client.get("/api/ready")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ready")

    def test_response_carries_request_id(self):
        r = self.client.get("/api/health")
        self.assertIn("X-Request-ID", r.headers)
        self.assertTrue(r.headers["X-Request-ID"])

    def test_incoming_request_id_is_echoed(self):
        r = self.client.get("/api/health", headers={"X-Request-ID": "abc123"})
        self.assertEqual(r.headers["X-Request-ID"], "abc123")

    def test_health_is_non_sensitive(self):
        r = self.client.get("/api/health")
        body = r.get_data(as_text=True).lower()
        for leak in ("secret", "database_url", "password", "token"):
            self.assertNotIn(leak, body)


if __name__ == "__main__":
    unittest.main()
