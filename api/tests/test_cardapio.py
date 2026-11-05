# Testes do cardápio (Ticket 1). Rodar: .venv/bin/python -m unittest test_cardapio


import logging
import tempfile
import unittest
from decimal import Decimal

from app import create_app, db
from models.crud import CRUD

logging.disable(logging.CRITICAL)


def _make_app():
    fd, path = tempfile.mkstemp(suffix=".db")
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "RATELIMIT_ENABLED": False,
    })


def _seed(app):
    # Um restaurante com dois pratos; valores literais são a fonte da verdade.
    with app.app_context():
        restaurante = CRUD.create.restaurante(nome="Cozinha Teste")
        categoria = CRUD.create.categoria(nome="Brasileira")
        CRUD.create.restaurante_categoria(
            id_restaurante=restaurante.id, id_categoria=categoria.id
        )
        menu = CRUD.create.cardapio(nome="Almoço", tipo="teste")
        prato1 = CRUD.create.prato(
            id_restaurante=restaurante.id, id_cardapio=menu.id,
            nome="Prato Feito", preco_unidade=Decimal("32.00"), quantidade=10,
        )
        prato2 = CRUD.create.prato(
            id_restaurante=restaurante.id, id_cardapio=menu.id,
            nome="Feijoada", preco_unidade=Decimal("28.50"), quantidade=5,
        )
        return restaurante.id, prato1.id, prato2.id


class CardapioTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.rest_id, self.prato1_id, self.prato2_id = _seed(self.app)
        self.client = self.app.test_client()

    def test_lista_restaurantes(self):
        response = self.client.get("/api/restaurantes")
        self.assertEqual(response.status_code, 200)
        restaurantes = response.get_json()["restaurantes"]
        nomes = {item["nome"] for item in restaurantes}
        self.assertIn("Cozinha Teste", nomes)

    def test_restaurante_com_pratos(self):
        response = self.client.get(f"/api/restaurantes/{self.rest_id}")
        self.assertEqual(response.status_code, 200)
        restaurante = response.get_json()["restaurante"]
        self.assertEqual(restaurante["nome"], "Cozinha Teste")
        precos = {prato["nome"]: prato["preco"] for prato in restaurante["pratos"]}
        self.assertEqual(precos["Prato Feito"], "32.00")
        self.assertEqual(precos["Feijoada"], "28.50")

    def test_restaurante_inexistente_404(self):
        response = self.client.get("/api/restaurantes/99999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["code"], "NOT_FOUND")

    def test_prato(self):
        response = self.client.get(f"/api/restaurantes/{self.rest_id}/pratos/{self.prato1_id}")
        self.assertEqual(response.status_code, 200)
        prato = response.get_json()["prato"]
        self.assertEqual(prato["nome"], "Prato Feito")
        self.assertEqual(prato["preco"], "32.00")

    def test_prato_inexistente_404(self):
        response = self.client.get(f"/api/restaurantes/{self.rest_id}/pratos/99999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["code"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
