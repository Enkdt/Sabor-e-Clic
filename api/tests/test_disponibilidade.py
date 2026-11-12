# DATA-003: prato disponível/indisponível; cozinheiro do restaurante dono liga/desliga.
# Rodar: .venv/bin/python -m unittest tests.test_disponibilidade

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
        rest = CRUD.create.restaurante(nome="Resto", slug="resto")
        rest2 = CRUD.create.restaurante(nome="Outro", slug="outro")
        menu = CRUD.create.cardapio(nome="M", tipo="t")
        prato = CRUD.create.prato(id_restaurante=rest.id, id_cardapio=menu.id,
                                  nome="Prato", slug="prato", preco_unidade=Decimal("30.00"), quantidade=5)
        cook = CRUD.create.cozinheiro(nome="Dono", email="dono@example.com", senha=PASSWORD, especialidade="g")
        CRUD.update.verificar_email(cook.id_usuario)
        CRUD.create.cozinheiro_restaurante(cook.id_usuario, rest.id)
        other = CRUD.create.cozinheiro(nome="Outro", email="estranho@example.com", senha=PASSWORD, especialidade="g")
        CRUD.update.verificar_email(other.id_usuario)
        CRUD.create.cozinheiro_restaurante(other.id_usuario, rest2.id)
        cliente = CRUD.create.cliente_com_endereco(
            nome="Ana", email="ana@example.com", senha=PASSWORD,
            rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
        )
        CRUD.update.verificar_email(cliente.id)
        return prato.id


class DisponibilidadeTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id = _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def test_default_available_in_json(self):
        r = self.client.get("/api/restaurantes/resto")
        prato = r.get_json()["restaurante"]["pratos"][0]
        self.assertTrue(prato["disponivel"])

    def test_owning_cook_can_disable(self):
        self._login("dono@example.com")
        r = self.client.patch(f"/api/pratos/{self.prato_id}/disponibilidade", json={"disponivel": False})
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertFalse(r.get_json()["prato"]["disponivel"])

    def test_other_restaurant_cook_cannot_toggle(self):
        self._login("estranho@example.com")
        r = self.client.patch(f"/api/pratos/{self.prato_id}/disponibilidade", json={"disponivel": False})
        self.assertEqual(r.status_code, 403, r.get_json())

    def test_cannot_order_unavailable_dish(self):
        self._login("dono@example.com")
        self.client.patch(f"/api/pratos/{self.prato_id}/disponibilidade", json={"disponivel": False})
        self.client.post("/api/logout")
        self._login("ana@example.com")
        r = self.client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato_id, "quantidade": 1}]})
        self.assertEqual(r.status_code, 409, r.get_json())
        self.assertEqual(r.get_json()["error"]["code"], "DISH_UNAVAILABLE")

    def test_validation_requires_boolean(self):
        self._login("dono@example.com")
        r = self.client.patch(f"/api/pratos/{self.prato_id}/disponibilidade", json={"disponivel": "sim"})
        self.assertEqual(r.status_code, 400, r.get_json())


if __name__ == "__main__":
    unittest.main()
