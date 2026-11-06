# Testes de favoritos (B2). Customer-only; idempotente; isolado por conta.
# Rodar: .venv/bin/python -m unittest test_favoritos

import logging
import tempfile
import unittest
from decimal import Decimal

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
        r = CRUD.create.restaurante(nome="Rest A")
        for email in ("ana@example.com", "bruno@example.com"):
            u = CRUD.create.cliente_com_endereco(
                nome="C", email=email, senha=PASSWORD,
                rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
            )
            CRUD.update.verificar_email(u.id)
        return r.id


class FavoritosTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.rid = _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def test_add_list_remove(self):
        self._login("ana@example.com")
        add = self.client.post("/api/favoritos", json={"id_restaurante": self.rid})
        self.assertIn(add.status_code, (200, 201), add.get_json())
        listing = self.client.get("/api/favoritos")
        self.assertEqual(listing.get_json()["favoritos"], [self.rid])
        # Idempotente.
        again = self.client.post("/api/favoritos", json={"id_restaurante": self.rid})
        self.assertEqual(self.client.get("/api/favoritos").get_json()["favoritos"], [self.rid])
        # Remove.
        self.client.delete(f"/api/favoritos/{self.rid}")
        self.assertEqual(self.client.get("/api/favoritos").get_json()["favoritos"], [])

    def test_isolated_per_account(self):
        self._login("ana@example.com")
        self.client.post("/api/favoritos", json={"id_restaurante": self.rid})
        self.client.post("/api/logout")
        self._login("bruno@example.com")
        self.assertEqual(self.client.get("/api/favoritos").get_json()["favoritos"], [])

    def test_requires_authentication(self):
        self.assertEqual(self.client.get("/api/favoritos").status_code, 401)


if __name__ == "__main__":
    unittest.main()
