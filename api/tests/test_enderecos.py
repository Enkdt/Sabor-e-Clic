# Testes do endpoint de endereços do cliente (Ticket 10/11).
# Rodar: .venv/bin/python -m unittest test_enderecos
#
# Cobre: cliente autenticado recebe o próprio endereço; sem sessão -> 401.

import logging
import tempfile
import unittest

from app import create_app
from models.crud import CRUD

logging.disable(logging.CRITICAL)

PASSWORD = "Senha!Forte123"


def _make_app():
    _, path = tempfile.mkstemp(suffix=".db")
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "RATELIMIT_ENABLED": False,
    })


def _seed(app):
    with app.app_context():
        user = CRUD.create.cliente_com_endereco(
            nome="Cliente Teste", email="cliente@example.com", senha=PASSWORD,
            rua="Rua Augusta", numero="120", cep="01304-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="República", complemento="Ap 12",
        )
        CRUD.update.verificar_email(user.id)


class EnderecosTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        _seed(self.app)
        self.client = self.app.test_client()

    def test_requires_authentication(self):
        response = self.client.get("/api/enderecos")
        self.assertEqual(response.status_code, 401, response.get_json())

    def test_returns_own_address(self):
        self.client.post("/api/login", json={"email": "cliente@example.com", "password": PASSWORD})
        response = self.client.get("/api/enderecos")
        self.assertEqual(response.status_code, 200, response.get_json())
        enderecos = response.get_json()["enderecos"]
        self.assertEqual(len(enderecos), 1)
        self.assertEqual(enderecos[0]["rua"], "Rua Augusta")
        self.assertEqual(enderecos[0]["numero"], "120")
        self.assertEqual(enderecos[0]["cidade"], "São Paulo")


if __name__ == "__main__":
    unittest.main()
