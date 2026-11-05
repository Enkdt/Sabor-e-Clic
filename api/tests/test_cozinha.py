# Testes do fluxo de cozinha por item (confirmar/negar). Cook/admin; dono do restaurante.
# Rodar: .venv/bin/python -m unittest tests.test_cozinha

import logging
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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
        cook = CRUD.create.cozinheiro(nome="Rafa", email="rafa@example.com", senha=PASSWORD, especialidade="Vegana")
        CRUD.update.verificar_email(cook.id_usuario)
        outro = CRUD.create.cozinheiro(nome="Marcos", email="marcos@example.com", senha=PASSWORD, especialidade="Carnes")
        CRUD.update.verificar_email(outro.id_usuario)
        restaurante = CRUD.create.restaurante(nome="Cozinha Teste", slug="cozinha-teste")
        CRUD.create.cozinheiro_restaurante(cook.id_usuario, restaurante.id)  # rafa gere; marcos não
        menu = CRUD.create.cardapio(nome="Almoço", tipo="t")
        prato = CRUD.create.prato(id_restaurante=restaurante.id, id_cardapio=menu.id, nome="Prato", preco_unidade=Decimal("30.00"), quantidade=10)
        cliente = CRUD.create.cliente_com_endereco(
            nome="Cliente", email="cliente@example.com", senha=PASSWORD,
            rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="Centro",
        )
        CRUD.update.verificar_email(cliente.id)
        return prato.id


class CozinhaTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id = _seed(self.app)
        self.client = self.app.test_client()
        # Cliente cria e paga um pedido (itens ficam 'aguardando' o cozinheiro).
        self.client.post("/api/login", json={"email": "cliente@example.com", "password": PASSWORD})
        created = self.client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato_id, "quantidade": 1}]})
        self.pedido_id = created.get_json()["pedido"]["id"]
        self.client.post(f"/api/pedidos/{self.pedido_id}/pagamento", json={"metodo": "entrega"})
        self.client.post("/api/logout")

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def test_cook_lists_and_confirms_item(self):
        self._login("rafa@example.com")
        listing = self.client.get("/api/cozinha/pedidos")
        self.assertEqual(listing.status_code, 200, listing.get_json())
        itens = listing.get_json()["itens"]
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["status"], "aguardando")
        confirm = self.client.post(f"/api/cozinha/itens/{self.pedido_id}/{self.prato_id}/confirmar")
        self.assertEqual(confirm.status_code, 200, confirm.get_json())
        self.assertEqual(confirm.get_json()["item"]["status"], "confirmado")

    def test_deny_item_refunds_saldo(self):
        with self.app.app_context():
            cliente = CRUD.read.usuario_por_email("cliente@example.com").cliente
            saldo_antes = Decimal(str(cliente.saldo))
        self._login("rafa@example.com")
        deny = self.client.post(f"/api/cozinha/itens/{self.pedido_id}/{self.prato_id}/negar", json={"motivo": "Sem ingredientes"})
        self.assertEqual(deny.status_code, 200, deny.get_json())
        self.assertEqual(deny.get_json()["item"]["status"], "negado")
        self.assertEqual(deny.get_json()["item"]["motivo_negacao"], "Sem ingredientes")
        with self.app.app_context():
            cliente = CRUD.read.usuario_por_email("cliente@example.com").cliente
            self.assertEqual(Decimal(str(cliente.saldo)), saldo_antes + Decimal("30.00"))

    def test_deny_requires_motivo(self):
        self._login("rafa@example.com")
        deny = self.client.post(f"/api/cozinha/itens/{self.pedido_id}/{self.prato_id}/negar", json={})
        self.assertEqual(deny.status_code, 400, deny.get_json())

    def test_other_cook_cannot_confirm(self):
        self._login("marcos@example.com")  # não gere este restaurante
        confirm = self.client.post(f"/api/cozinha/itens/{self.pedido_id}/{self.prato_id}/confirmar")
        self.assertEqual(confirm.status_code, 403, confirm.get_json())

    def test_cannot_confirm_twice(self):
        self._login("rafa@example.com")
        self.client.post(f"/api/cozinha/itens/{self.pedido_id}/{self.prato_id}/confirmar")
        again = self.client.post(f"/api/cozinha/itens/{self.pedido_id}/{self.prato_id}/confirmar")
        self.assertEqual(again.status_code, 409, again.get_json())

    def test_item_reaches_entregue_by_time(self):
        # Confirma e força confirmado_em para o passado; o estado efetivo deve ser 'entregue'.
        self._login("rafa@example.com")
        self.client.post(f"/api/cozinha/itens/{self.pedido_id}/{self.prato_id}/confirmar")
        with self.app.app_context():
            CRUD.update.pedido_prato(
                (self.pedido_id, self.prato_id),
                {"confirmado_em": datetime.now(timezone.utc) - timedelta(minutes=5)},
            )
        self.client.post("/api/logout")
        self._login("cliente@example.com")
        read = self.client.get(f"/api/pedidos/{self.pedido_id}")
        item = read.get_json()["pedido"]["itens"][0]
        self.assertEqual(item["status"], "entregue")
        self.assertEqual(read.get_json()["pedido"]["status"], "entregue")

    def test_customer_forbidden(self):
        self._login("cliente@example.com")
        listing = self.client.get("/api/cozinha/pedidos")
        self.assertEqual(listing.status_code, 403, listing.get_json())

    def test_requires_authentication(self):
        response = self.client.get("/api/cozinha/pedidos")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
