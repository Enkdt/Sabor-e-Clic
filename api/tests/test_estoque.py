# Testes do estoque (Ticket 14) — CRUD de ingredientes, admin-only.
# Rodar: .venv/bin/python -m unittest test_estoque

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
        admin = CRUD.create.funcionario(
            nome="Admin", email="admin@example.com", senha=PASSWORD, nivel_permissao=5,
        )
        CRUD.update.verificar_email(admin.id_usuario)
        cliente = CRUD.create.cliente_com_endereco(
            nome="Cliente", email="cliente@example.com", senha=PASSWORD,
            rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="Centro",
        )
        CRUD.update.verificar_email(cliente.id)


class EstoqueTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def test_admin_creates_and_lists(self):
        self._login("admin@example.com")
        created = self.client.post("/api/ingredientes", json={
            "nome": "Arroz integral", "validade": "2027-09-24", "quantidade": 20, "unidade": "kg",
        })
        self.assertEqual(created.status_code, 201, created.get_json())
        listing = self.client.get("/api/ingredientes")
        self.assertEqual(listing.status_code, 200)
        nomes = [i["nome"] for i in listing.get_json()["ingredientes"]]
        self.assertIn("Arroz integral", nomes)

    def test_rejects_negative_quantity_and_bad_unit(self):
        self._login("admin@example.com")
        neg = self.client.post("/api/ingredientes", json={
            "nome": "X", "validade": "2027-01-01", "quantidade": -1, "unidade": "kg",
        })
        self.assertEqual(neg.status_code, 400)
        self.assertIn("quantidade", neg.get_json()["error"]["fields"])
        bad_unit = self.client.post("/api/ingredientes", json={
            "nome": "X", "validade": "2027-01-01", "quantidade": 1, "unidade": "toneladas",
        })
        self.assertEqual(bad_unit.status_code, 400)
        self.assertIn("unidade", bad_unit.get_json()["error"]["fields"])

    def test_edit_updates_quantity(self):
        self._login("admin@example.com")
        created = self.client.post("/api/ingredientes", json={
            "nome": "Tofu", "validade": "2026-11-20", "quantidade": 8, "unidade": "kg",
        }).get_json()["ingrediente"]
        edited = self.client.patch(f"/api/ingredientes/{created['id']}", json={"quantidade": 0})
        self.assertEqual(edited.status_code, 200, edited.get_json())
        self.assertEqual(edited.get_json()["ingrediente"]["quantidade"], "0.00")

    def test_customer_forbidden(self):
        self._login("cliente@example.com")
        response = self.client.get("/api/ingredientes")
        self.assertEqual(response.status_code, 403, response.get_json())

    def test_requires_authentication(self):
        response = self.client.post("/api/ingredientes", json={
            "nome": "X", "validade": "2027-01-01", "quantidade": 1, "unidade": "kg",
        })
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
