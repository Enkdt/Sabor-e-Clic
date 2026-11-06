# Testes do dashboard (Ticket 14) — métricas derivadas de pedidos reais, admin-only.
# Rodar: .venv/bin/python -m unittest test_dashboard

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
        admin = CRUD.create.funcionario(
            nome="Admin", email="admin@example.com", senha=PASSWORD, nivel_permissao=5,
        )
        CRUD.update.verificar_email(admin.id_usuario)
        restaurante = CRUD.create.restaurante(nome="Cozinha Teste")
        menu = CRUD.create.cardapio(nome="Almoço", tipo="teste")
        prato = CRUD.create.prato(
            id_restaurante=restaurante.id, id_cardapio=menu.id,
            nome="Prato", preco_unidade=Decimal("50.00"), quantidade=10,
        )
        cliente = CRUD.create.cliente_com_endereco(
            nome="Cliente", email="cliente@example.com", senha=PASSWORD,
            rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="Centro",
        )
        CRUD.update.verificar_email(cliente.id)
        return prato.id


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id = _seed(self.app)
        self.client = self.app.test_client()

    def test_metrics_reflect_paid_orders(self):
        # Cliente cria e paga um pedido.
        self.client.post("/api/login", json={"email": "cliente@example.com", "password": PASSWORD})
        created = self.client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato_id, "quantidade": 2}]})
        pedido_id = created.get_json()["pedido"]["id"]
        self.client.post(f"/api/pedidos/{pedido_id}/pagamento", json={"metodo": "entrega"})
        self.client.post("/api/logout")

        # Admin consulta o dashboard.
        self.client.post("/api/login", json={"email": "admin@example.com", "password": PASSWORD})
        response = self.client.get("/api/dashboard?periodo=30")
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()
        self.assertEqual(data["kpis"]["pedidos_pagos"], 1)
        self.assertEqual(data["kpis"]["receita_total"], "100.00")
        self.assertEqual(data["kpis"]["ticket_medio"], "100.00")
        # Receita atribuída ao restaurante correto.
        self.assertEqual(data["receita_por_restaurante"][0]["label"], "Cozinha Teste")
        self.assertEqual(data["receita_por_restaurante"][0]["value"], "100.00")

    def test_customer_forbidden(self):
        self.client.post("/api/login", json={"email": "cliente@example.com", "password": PASSWORD})
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
