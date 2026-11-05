# Testes: recarga de saldo (simulação), validação de formato de agendamento, slug de prato, autor da avaliação.
# Rodar: .venv/bin/python -m unittest tests.test_saldo_slug

import logging
import tempfile
import unittest
from datetime import date, timedelta
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
        menu = CRUD.create.cardapio(nome="M", tipo="t")
        prato = CRUD.create.prato(id_restaurante=rest.id, id_cardapio=menu.id, nome="Pizza Margherita", slug="pizza-margherita", preco_unidade=Decimal("40.00"), quantidade=10)
        c = CRUD.create.cliente_com_endereco(
            nome="Ana Demo", email="ana@example.com", senha=PASSWORD,
            rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
        )
        CRUD.update.verificar_email(c.id)
        bancada = CRUD.create.bancada(preco_hora=Decimal("60.00"))
        from datetime import time as _t
        CRUD.create.bancada_horario_disponivel(id_bancada=bancada.id, id=1, inicio=_t(8, 0), fim=_t(18, 0))
        return prato.id, bancada.id


class SaldoSlugTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id, self.bancada_id = _seed(self.app)
        self.client = self.app.test_client()
        self.client.post("/api/login", json={"email": "ana@example.com", "password": PASSWORD})

    def test_add_balance(self):
        r = self.client.post("/api/perfil/saldo", json={"valor": 50})
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(r.get_json()["saldo"], "250.00")  # 200 inicial + 50

    def test_add_balance_rejects_out_of_range(self):
        self.assertEqual(self.client.post("/api/perfil/saldo", json={"valor": 0}).status_code, 400)
        self.assertEqual(self.client.post("/api/perfil/saldo", json={"valor": 99999}).status_code, 400)
        self.assertEqual(self.client.post("/api/perfil/saldo", json={"valor": "abc"}).status_code, 400)

    def test_booking_rejects_date_only(self):
        # Sem hora (só data) deve ser rejeitado.
        amanha = (date.today() + timedelta(days=2)).isoformat()
        r = self.client.post(f"/api/bancadas/{self.bancada_id}/agendamentos", json={"inicio": amanha, "fim": amanha})
        self.assertEqual(r.status_code, 400, r.get_json())

    def test_booking_rejects_garbage(self):
        r = self.client.post(f"/api/bancadas/{self.bancada_id}/agendamentos", json={"inicio": "lixo", "fim": "123"})
        self.assertEqual(r.status_code, 400, r.get_json())

    def test_dish_fetch_by_slug(self):
        r = self.client.get("/api/restaurantes/resto/pratos/pizza-margherita")
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(r.get_json()["prato"]["id"], self.prato_id)
        self.assertEqual(r.get_json()["prato"]["slug"], "pizza-margherita")

    def test_review_includes_author_name(self):
        # Cria e paga um pedido, confirma item e avalia; a avaliação pública traz o nome.
        pid = self.client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato_id, "quantidade": 1}]}).get_json()["pedido"]["id"]
        self.client.post(f"/api/pedidos/{pid}/pagamento", json={"metodo": "entrega"})
        self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": 5, "comentario": "Ótimo"})
        pub = self.client.get(f"/api/pratos/{self.prato_id}/avaliacoes")
        self.assertEqual(pub.status_code, 200, pub.get_json())
        self.assertEqual(pub.get_json()["avaliacoes"][0]["cliente"], "Ana Demo")


if __name__ == "__main__":
    unittest.main()
