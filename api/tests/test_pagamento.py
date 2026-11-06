# Testes de pagamento (Ticket 6, placeholder "pagar na entrega").
# Rodar: .venv/bin/python -m unittest test_pagamento
#

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
        prato = CRUD.create.prato(
            id_restaurante=restaurante.id, id_cardapio=menu.id,
            nome="Prato Feito", preco_unidade=Decimal("32.00"), quantidade=10,
        )
        user = CRUD.create.cliente_com_endereco(
            nome="Cliente Teste", email="cliente@example.com", senha=PASSWORD,
            rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="Centro",
        )
        CRUD.update.verificar_email(user.id)
        return prato.id


class PagamentoTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id = _seed(self.app)
        self.client = self.app.test_client()
        self.client.post("/api/login", json={"email": "cliente@example.com", "password": PASSWORD})
        created = self.client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato_id, "quantidade": 1}]})
        self.pedido_id = created.get_json()["pedido"]["id"]

    def test_pay_once_debits_saldo(self):
        response = self.client.post(f"/api/pedidos/{self.pedido_id}/pagamento", json={"metodo": "entrega"})
        self.assertEqual(response.status_code, 200, response.get_json())
        # Pago vira True; o status mostrado passa a refletir o andamento (itens 'aguardando' cozinheiro).
        self.assertTrue(response.get_json()["pedido"]["pago"])
        self.assertEqual(response.get_json()["pedido"]["status"], "aguardando")
        # Saldo foi debitado: 200.00 inicial - 32.00 = 168.00.
        with self.app.app_context():
            cliente = CRUD.read.usuario_por_email("cliente@example.com").cliente
            self.assertEqual(str(cliente.saldo), "168.00")

    def test_pay_twice_is_noop(self):
        first = self.client.post(f"/api/pedidos/{self.pedido_id}/pagamento", json={"metodo": "entrega"})
        self.assertEqual(first.status_code, 200)
        second = self.client.post(f"/api/pedidos/{self.pedido_id}/pagamento", json={"metodo": "entrega"})
        self.assertEqual(second.status_code, 200, second.get_json())
        self.assertTrue(second.get_json()["pedido"]["pago"])
        # Não debita de novo: saldo continua 168.00.
        with self.app.app_context():
            cliente = CRUD.read.usuario_por_email("cliente@example.com").cliente
            self.assertEqual(str(cliente.saldo), "168.00")

    def test_insufficient_funds_blocked(self):
        # Zera o saldo do cliente e tenta pagar.
        with self.app.app_context():
            cliente = CRUD.read.usuario_por_email("cliente@example.com").cliente
            CRUD.update.cliente(cliente.id_usuario, {"saldo": Decimal("0.00")})
        response = self.client.post(f"/api/pedidos/{self.pedido_id}/pagamento", json={"metodo": "entrega"})
        self.assertEqual(response.status_code, 402, response.get_json())
        self.assertEqual(response.get_json()["error"]["code"], "INSUFFICIENT_FUNDS")


if __name__ == "__main__":
    unittest.main()
