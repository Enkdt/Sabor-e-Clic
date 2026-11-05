# Testes do pedido (Ticket 4). Rodar: .venv/bin/python -m unittest test_pedidos
#
# Cobre: criação de pedido com total calculado no servidor, recusa de preço
# enviado pelo cliente, e bloqueio de um cliente ler o pedido de outro (403).

import logging
import tempfile
import unittest
from decimal import Decimal

from app import create_app, db
from models.crud import CRUD

logging.disable(logging.CRITICAL)

PASSWORD = "Senha!Forte123"


def _make_app():
    fd, path = tempfile.mkstemp(suffix=".db")
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "RATELIMIT_ENABLED": False,
    })


def _seed(app):
    with app.app_context():
        restaurante = CRUD.create.restaurante(nome="Cozinha Teste")
        menu = CRUD.create.cardapio(nome="Almoço", tipo="teste")
        prato1 = CRUD.create.prato(
            id_restaurante=restaurante.id, id_cardapio=menu.id,
            nome="Prato Feito", preco_unidade=Decimal("32.00"), quantidade=10,
        )
        prato2 = CRUD.create.prato(
            id_restaurante=restaurante.id, id_cardapio=menu.id,
            nome="Feijoada", preco_unidade=Decimal("28.50"), quantidade=5,
        )
        for email in ("cliente1@example.com", "cliente2@example.com"):
            user = CRUD.create.cliente_com_endereco(
                nome="Cliente Teste", email=email, senha=PASSWORD,
                rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
                estado="SP", cidade="São Paulo", bairro="Centro",
            )
            CRUD.update.verificar_email(user.id)
        return prato1.id, prato2.id


def _login(client, email):
    response = client.post("/api/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.get_json()


class PedidoTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato1_id, self.prato2_id = _seed(self.app)

    def _client(self, email):
        client = self.app.test_client()
        _login(client, email)
        return client

    def test_place_order_computes_total_server_side(self):
        client = self._client("cliente1@example.com")
        # 2 × 32.00 + 1 × 28.50 = 92.50 (fonte da verdade: cálculo manual)
        response = client.post("/api/pedidos", json={"itens": [
            {"id_prato": self.prato1_id, "quantidade": 2},
            {"id_prato": self.prato2_id, "quantidade": 1},
        ]})
        self.assertEqual(response.status_code, 201, response.get_json())
        pedido = response.get_json()["pedido"]
        self.assertEqual(pedido["total"], "92.50")
        self.assertEqual(pedido["status"], "preparando")

    def test_price_is_server_authoritative(self):
        # Preço enviado pelo cliente deve ser ignorado; vale só o preço armazenado.
        client = self._client("cliente1@example.com")
        response = client.post("/api/pedidos", json={"itens": [
            {"id_prato": self.prato1_id, "quantidade": 1, "preco": 0.01},
        ]})
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["pedido"]["total"], "32.00")

    def test_empty_items_rejected(self):
        client = self._client("cliente1@example.com")
        response = client.post("/api/pedidos", json={"itens": []})
        self.assertEqual(response.status_code, 400)

    def test_list_orders_returns_own(self):
        client = self._client("cliente1@example.com")
        client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato1_id, "quantidade": 1}]})
        response = client.get("/api/pedidos")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["pedidos"]), 1)

    def test_cross_customer_order_is_forbidden(self):
        owner = self._client("cliente1@example.com")
        created = owner.post("/api/pedidos", json={"itens": [{"id_prato": self.prato1_id, "quantidade": 1}]})
        pedido_id = created.get_json()["pedido"]["id"]

        intruder = self._client("cliente2@example.com")
        response = intruder.get(f"/api/pedidos/{pedido_id}")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"]["code"], "PERMISSION_DENIED")


if __name__ == "__main__":
    unittest.main()
