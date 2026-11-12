# API-001: erros HTTP em /api/* retornam o envelope JSON padrão.
# Rodar: .venv/bin/python -m unittest tests.test_api_errors

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


class ApiErrorEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_unknown_api_route_returns_json_404(self):
        r = self.client.get("/api/rota-que-nao-existe")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.mimetype, "application/json")
        self.assertIn("error", r.get_json())
        self.assertIn("code", r.get_json()["error"])

    def test_wrong_method_returns_json_405_with_allow(self):
        # /api/login aceita POST; GET deve dar 405 em JSON com cabeçalho Allow.
        r = self.client.get("/api/login")
        self.assertEqual(r.status_code, 405)
        self.assertEqual(r.mimetype, "application/json")
        self.assertIn("error", r.get_json())
        self.assertIn("Allow", r.headers)


if __name__ == "__main__":
    unittest.main()
