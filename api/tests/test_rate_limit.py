# SEC-003: limites por email em reset/reenvio (além do limite por IP).
# Rodar: .venv/bin/python -m unittest tests.test_rate_limit

import logging
import tempfile
import unittest

from app import create_app
from models.crud import CRUD

logging.disable(logging.CRITICAL)


def _make_app():
    _, path = tempfile.mkstemp(suffix=".db")
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        # Rate limiting LIGADO para este teste, com store em memória.
        "RATELIMIT_ENABLED": True,
        "RATELIMIT_STORAGE_URI": "memory://",
    })


class PerEmailRateLimitTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_password_reset_limited_per_email(self):
        # O limite é 3/hora por email; a 4a tentativa para o MESMO email → 429.
        payload = {"email": "alvo@example.com"}
        codes = [self.client.post("/api/password-reset/request", json=payload).status_code
                 for _ in range(4)]
        self.assertEqual(codes[:3], [200, 200, 200], codes)
        self.assertEqual(codes[3], 429, codes)


if __name__ == "__main__":
    unittest.main()
