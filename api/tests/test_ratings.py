# UX-001: avaliação real agregada por restaurante (nunca estrelas fixas).
# Rodar: .venv/bin/python -m unittest tests.test_ratings

import logging
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
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
        prato = CRUD.create.prato(id_restaurante=rest.id, id_cardapio=menu.id,
                                  nome="P", slug="p", preco_unidade=Decimal("30.00"), quantidade=10)
        user = CRUD.create.cliente_com_endereco(
            nome="Ana", email="ana@example.com", senha=PASSWORD,
            rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
        )
        CRUD.update.verificar_email(user.id)
        return rest.slug, prato.id


class RatingTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.slug, self.prato_id = _seed(self.app)
        self.client = self.app.test_client()
        self.client.post("/api/login", json={"email": "ana@example.com", "password": PASSWORD})

    def _pedir_pagar_entregar_avaliar(self, nota):
        pid = self.client.post("/api/pedidos", json={"itens": [{"id_prato": self.prato_id, "quantidade": 1}]}).get_json()["pedido"]["id"]
        self.client.post(f"/api/pedidos/{pid}/pagamento", json={"metodo": "entrega"})
        with self.app.app_context():
            CRUD.update.pedido_prato((pid, self.prato_id),
                                     {"status": "confirmado", "confirmado_em": datetime.now(timezone.utc) - timedelta(hours=1)})
        self.client.post(f"/api/pedidos/{pid}/avaliacao", json={"id_prato": self.prato_id, "nota": nota})

    def test_no_reviews_returns_null_average(self):
        r = self.client.get(f"/api/restaurantes/{self.slug}")
        data = r.get_json()["restaurante"]
        self.assertIsNone(data["avaliacao_media"])
        self.assertEqual(data["avaliacao_total"], 0)

    def test_average_reflects_reviews(self):
        self._pedir_pagar_entregar_avaliar(5)
        self._pedir_pagar_entregar_avaliar(3)
        r = self.client.get(f"/api/restaurantes/{self.slug}")
        data = r.get_json()["restaurante"]
        self.assertEqual(data["avaliacao_media"], 4.0)
        self.assertEqual(data["avaliacao_total"], 2)

    def test_list_endpoint_includes_rating(self):
        self._pedir_pagar_entregar_avaliar(4)
        r = self.client.get("/api/restaurantes")
        resto = next(x for x in r.get_json()["restaurantes"] if x["slug"] == self.slug)
        self.assertEqual(resto["avaliacao_media"], 4.0)
        self.assertEqual(resto["avaliacao_total"], 1)


if __name__ == "__main__":
    unittest.main()
