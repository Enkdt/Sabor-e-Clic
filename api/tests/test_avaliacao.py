# Testes de avaliações (Ticket 12). Dono do pedido; só pedidos pagos; uma por pedido.
# Rodar: .venv/bin/python -m unittest test_avaliacao

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
        restaurante = CRUD.create.restaurante(nome="Cozinha Teste")
        menu = CRUD.create.cardapio(nome="Almoço", tipo="t")
        prato = CRUD.create.prato(id_restaurante=restaurante.id, id_cardapio=menu.id, nome="Prato", preco_unidade=Decimal("30.00"), quantidade=10)
        for email in ("ana@example.com", "bruno@example.com"):
            u = CRUD.create.cliente_com_endereco(
                nome="C", email=email, senha=PASSWORD,
                rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
            )
            CRUD.update.verificar_email(u.id)
        return prato.id


class AvaliacaoTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id = _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def _novo_pedido(self, pay=True):
        created = self.client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato_id, "quantidade": 1}]})
        pid = created.get_json()["pedido"]["id"]
        if pay:
            self.client.post(f"/api/pedidos/{pid}/pagamento", json={"metodo": "entrega"})
        return pid

    def test_review_paid_order(self):
        self._login("ana@example.com")
        pid = self._novo_pedido(pay=True)
        response = self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": 5, "comentario": "Ótimo!"})
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["avaliacao"]["nota"], 5)
        # A avaliação referencia o prato e o restaurante dele.
        self.assertEqual(response.get_json()["avaliacao"]["id_prato"], self.prato_id)
        self.assertTrue(response.get_json()["avaliacao"]["restaurante"])
        # GET devolve a lista de avaliações do pedido.
        got = self.client.get(f"/api/pedidos/{pid}/avaliacao")
        self.assertEqual(got.get_json()["avaliacoes"][0]["nota"], 5)

    def test_cannot_review_unpaid_order(self):
        self._login("ana@example.com")
        pid = self._novo_pedido(pay=False)
        response = self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": 4})
        self.assertEqual(response.status_code, 409, response.get_json())

    def test_duplicate_review_rejected(self):
        self._login("ana@example.com")
        pid = self._novo_pedido(pay=True)
        self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": 5})
        dup = self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": 3})
        self.assertEqual(dup.status_code, 409, dup.get_json())

    def test_invalid_rating_rejected(self):
        self._login("ana@example.com")
        pid = self._novo_pedido(pay=True)
        response = self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": 9})
        self.assertEqual(response.status_code, 400, response.get_json())

    def test_cannot_review_prato_not_in_order(self):
        self._login("ana@example.com")
        pid = self._novo_pedido(pay=True)
        response = self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id + 999, "nota": 5})
        self.assertEqual(response.status_code, 400, response.get_json())

    def test_cannot_review_another_customers_order(self):
        self._login("ana@example.com")
        pid = self._novo_pedido(pay=True)
        self.client.post("/api/logout")
        self._login("bruno@example.com")
        response = self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": 5})
        self.assertEqual(response.status_code, 403, response.get_json())


if __name__ == "__main__":
    unittest.main()
