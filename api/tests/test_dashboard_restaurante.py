# Mini dashboard por restaurante: /api/restaurantes/<id>/metricas.
# KPIs escopados ao restaurante; ownership: admin vê qualquer um, cozinheiro só os seus.
# Rodar: .venv/bin/python -m unittest tests.test_dashboard_restaurante

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
    """Dois restaurantes; cook A afiliado ao rest A, cook B ao rest B; um pedido pago
    com 2 unidades de um prato do rest A. Retorna ids usados nos testes."""
    with app.app_context():
        admin = CRUD.create.funcionario(
            nome="Admin", email="admin@example.com", senha=PASSWORD, nivel_permissao=5,
        )
        CRUD.update.verificar_email(admin.id_usuario)

        rest_a = CRUD.create.restaurante(nome="Cozinha A", slug="cozinha-a")
        rest_b = CRUD.create.restaurante(nome="Cozinha B", slug="cozinha-b")
        menu = CRUD.create.cardapio(nome="Almoço", tipo="teste")
        prato_a = CRUD.create.prato(
            id_restaurante=rest_a.id, id_cardapio=menu.id,
            nome="Prato A", slug="prato-a", preco_unidade=Decimal("50.00"), quantidade=10,
        )

        cook_a = CRUD.create.cozinheiro(
            nome="Cook A", email="cooka@example.com", senha=PASSWORD, especialidade="g",
        )
        CRUD.update.verificar_email(cook_a.id_usuario)
        CRUD.create.cozinheiro_restaurante(cook_a.id_usuario, rest_a.id)

        cook_b = CRUD.create.cozinheiro(
            nome="Cook B", email="cookb@example.com", senha=PASSWORD, especialidade="g",
        )
        CRUD.update.verificar_email(cook_b.id_usuario)
        CRUD.create.cozinheiro_restaurante(cook_b.id_usuario, rest_b.id)

        cliente = CRUD.create.cliente_com_endereco(
            nome="Cliente", email="cliente@example.com", senha=PASSWORD,
            rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="Centro",
        )
        CRUD.update.verificar_email(cliente.id)
        return {"rest_a": rest_a.id, "rest_b": rest_b.id, "prato_a": prato_a.id}


class RestaurantMetricsTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ids = _seed(self.app)
        self.client = self.app.test_client()
        # Cliente paga um pedido de 2 unidades do prato do restaurante A.
        self.client.post("/api/login", json={"email": "cliente@example.com", "password": PASSWORD})
        created = self.client.post(
            "/api/pedidos", json={"itens": [{"id_prato": self.ids["prato_a"], "quantidade": 2}]}
        )
        pedido_id = created.get_json()["pedido"]["id"]
        self.client.post(f"/api/pedidos/{pedido_id}/pagamento", json={"metodo": "entrega"})
        self.client.post("/api/logout")

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def test_admin_sees_scoped_kpis(self):
        self._login("admin@example.com")
        r = self.client.get(f"/api/restaurantes/{self.ids['rest_a']}/metricas?periodo=30")
        self.assertEqual(r.status_code, 200, r.get_json())
        data = r.get_json()
        self.assertEqual(data["restaurante"]["nome"], "Cozinha A")
        self.assertEqual(data["kpis"]["pedidos_pagos"], 1)
        self.assertEqual(data["kpis"]["itens_vendidos"], 2)
        self.assertEqual(data["kpis"]["receita_total"], "100.00")
        self.assertEqual(data["kpis"]["ticket_medio"], "100.00")
        self.assertEqual(data["receita_por_prato"][0]["label"], "Prato A")
        self.assertEqual(data["receita_por_prato"][0]["value"], "100.00")

    def test_restaurant_b_has_no_revenue(self):
        self._login("admin@example.com")
        r = self.client.get(f"/api/restaurantes/{self.ids['rest_b']}/metricas")
        self.assertEqual(r.status_code, 200, r.get_json())
        data = r.get_json()
        self.assertEqual(data["kpis"]["pedidos_pagos"], 0)
        self.assertEqual(data["kpis"]["receita_total"], "0.00")
        self.assertEqual(data["receita_por_prato"], [])

    def test_affiliated_cook_sees_own_restaurant(self):
        self._login("cooka@example.com")
        r = self.client.get(f"/api/restaurantes/{self.ids['rest_a']}/metricas")
        self.assertEqual(r.status_code, 200, r.get_json())

    def test_non_affiliated_cook_forbidden(self):
        # Cook B não gerencia o restaurante A.
        self._login("cookb@example.com")
        r = self.client.get(f"/api/restaurantes/{self.ids['rest_a']}/metricas")
        self.assertEqual(r.status_code, 403, r.get_json())

    def test_customer_forbidden(self):
        self._login("cliente@example.com")
        r = self.client.get(f"/api/restaurantes/{self.ids['rest_a']}/metricas")
        self.assertEqual(r.status_code, 403, r.get_json())

    def test_unknown_restaurant_404(self):
        self._login("admin@example.com")
        r = self.client.get("/api/restaurantes/999999/metricas")
        self.assertEqual(r.status_code, 404, r.get_json())


if __name__ == "__main__":
    unittest.main()
