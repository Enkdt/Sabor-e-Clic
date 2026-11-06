# Testes de regressão do cadastro. Rodar: .venv/bin/python -m unittest test_cadastro

import logging
import tempfile
import unittest

from app import create_app, db
from models import Usuario

logging.disable(logging.CRITICAL)  # silencia o erro esperado da thread de email

_VALID_PAYLOAD = {
    "name": "Joao", "surname": "Silva", "email": "joao@example.com",
    "password": "Senha!Forte123", "password_confirmation": "Senha!Forte123",
    "cep": "01001-000", "country": "Brasil", "street": "Rua A", "number": "10",
    "neighborhood": "Centro", "city": "Sao Paulo", "state": "SP", "extra": "",
}


def _make_app(**overrides):
    fd, path = tempfile.mkstemp(suffix=".db")
    config = {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "RATELIMIT_ENABLED": False,
        # Servidor SMTP inalcançável: o envio falha de propósito.
        "MAIL_SERVER": "127.0.0.1",
        "MAIL_PORT": 2,
    }
    config.update(overrides)
    return create_app(config)


class CadastroTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_cadastro_succeeds_even_when_email_fails(self):
        # O bug original: cadastro devolvia 500 quando o SMTP falhava.
        response = self.client.post("/api/cadastro", json=_VALID_PAYLOAD)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])
        with self.app.app_context():
            user = db.session.execute(
                db.select(Usuario).where(Usuario.email == "joao@example.com")
            ).scalar_one_or_none()
            self.assertIsNotNone(user)
            self.assertFalse(user.email_verificado)

    def test_duplicate_email_is_rejected(self):
        self.client.post("/api/cadastro", json=_VALID_PAYLOAD)
        response = self.client.post("/api/cadastro", json=_VALID_PAYLOAD)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "USER_EXISTS")

    def test_password_mismatch_is_rejected(self):
        payload = dict(_VALID_PAYLOAD, password_confirmation="Outra!Senha123")
        response = self.client.post("/api/cadastro", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "PASSWORD_DOES_NOT_MATCH")

    def test_weak_password_is_rejected(self):
        payload = dict(_VALID_PAYLOAD, password="12345678", password_confirmation="12345678")
        response = self.client.post("/api/cadastro", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "WEAK_PASSWORD")

    def test_missing_fields_are_rejected(self):
        response = self.client.post("/api/cadastro", json={"name": "Joao"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "MISSING_INFO")


if __name__ == "__main__":
    unittest.main()
