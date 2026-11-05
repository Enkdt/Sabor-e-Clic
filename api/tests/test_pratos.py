# Testes de gestão de pratos e filiação cozinheiro↔restaurante.
# Rodar: .venv/bin/python -m unittest tests.test_pratos

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
        admin = CRUD.create.funcionario(nome="Admin", email="admin@example.com", senha=PASSWORD, nivel_permissao=5)
        CRUD.update.verificar_email(admin.id_usuario)
        for email in ("rafa@example.com", "outro@example.com"):
            c = CRUD.create.cozinheiro(nome="Cook", email=email, senha=PASSWORD, especialidade="geral")
            CRUD.update.verificar_email(c.id_usuario)
        r1 = CRUD.create.restaurante(nome="Cantina Um", slug="cantina-um")
        r2 = CRUD.create.restaurante(nome="Bistro Dois", slug="bistro-dois")
        # rafa gerencia só o r1
        rafa = CRUD.read.cozinheiros(filters=None)
        rafa_id = next(c.id_usuario for c in rafa if c.usuario.email == "rafa@example.com")
        CRUD.create.cozinheiro_restaurante(rafa_id, r1.id)
        return {"r1": r1.id, "r2": r2.id, "rafa": rafa_id}


class PratosTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ids = _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def test_cook_creates_dish_in_own_restaurant(self):
        self._login("rafa@example.com")
        r = self.client.post(f"/api/restaurantes/{self.ids['r1']}/pratos", json={
            "nome": "Lasanha", "preco": "32.50", "quantidade": 10, "descricao": "Caseira",
        })
        self.assertEqual(r.status_code, 201, r.get_json())
        self.assertEqual(r.get_json()["prato"]["nome"], "Lasanha")
        self.assertEqual(r.get_json()["prato"]["id_restaurante"], self.ids["r1"])

    def test_cook_cannot_create_in_other_restaurant(self):
        self._login("rafa@example.com")
        r = self.client.post(f"/api/restaurantes/{self.ids['r2']}/pratos", json={
            "nome": "X", "preco": "10", "quantidade": 1,
        })
        self.assertEqual(r.status_code, 403, r.get_json())

    def test_admin_can_edit_any_dish(self):
        self._login("rafa@example.com")
        pid = self.client.post(f"/api/restaurantes/{self.ids['r1']}/pratos", json={
            "nome": "Sopa", "preco": "12", "quantidade": 5,
        }).get_json()["prato"]["id"]
        self.client.post("/api/logout")
        self._login("admin@example.com")
        edited = self.client.patch(f"/api/pratos/{pid}", json={"preco": "15"})
        self.assertEqual(edited.status_code, 200, edited.get_json())
        self.assertEqual(edited.get_json()["prato"]["preco"], "15.00")

    def test_other_cook_cannot_edit_dish(self):
        self._login("rafa@example.com")
        pid = self.client.post(f"/api/restaurantes/{self.ids['r1']}/pratos", json={
            "nome": "Bolo", "preco": "8", "quantidade": 3,
        }).get_json()["prato"]["id"]
        self.client.post("/api/logout")
        self._login("outro@example.com")
        edited = self.client.patch(f"/api/pratos/{pid}", json={"preco": "1"})
        self.assertEqual(edited.status_code, 403, edited.get_json())

    def test_admin_creates_restaurant_with_slug(self):
        self._login("admin@example.com")
        r = self.client.post("/api/restaurantes", json={"nome": "Novo Lugar"})
        self.assertEqual(r.status_code, 201, r.get_json())
        self.assertEqual(r.get_json()["restaurante"]["slug"], "novo-lugar")

    def test_restaurant_fetch_by_slug(self):
        got = self.client.get("/api/restaurantes/cantina-um")
        self.assertEqual(got.status_code, 200, got.get_json())
        self.assertEqual(got.get_json()["restaurante"]["id"], self.ids["r1"])

    def test_admin_associates_cook_to_restaurant(self):
        self._login("admin@example.com")
        r = self.client.post(f"/api/usuarios/cozinheiros/{self.ids['rafa']}/restaurantes", json={"id_restaurante": self.ids["r2"]})
        self.assertEqual(r.status_code, 200, r.get_json())
        slugs = [x["id"] for x in r.get_json()["cozinheiro"]["restaurantes"]]
        self.assertIn(self.ids["r2"], slugs)

    def test_cook_cannot_associate(self):
        self._login("rafa@example.com")
        r = self.client.post(f"/api/usuarios/cozinheiros/{self.ids['rafa']}/restaurantes", json={"id_restaurante": self.ids["r2"]})
        self.assertEqual(r.status_code, 403, r.get_json())


if __name__ == "__main__":
    unittest.main()
