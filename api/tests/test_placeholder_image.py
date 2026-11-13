# Placeholder de imagem: entidades sem foto própria recebem a imagem padrão (stock).
# Rodar: .venv/bin/python -m unittest tests.test_placeholder_image

import logging
import tempfile
import unittest
from decimal import Decimal

from app import create_app
from models.crud import CRUD
import placeholders

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


def _seed_sem_imagem(app):
    with app.app_context():
        rest = CRUD.create.restaurante(nome="Sem Foto", slug="sem-foto")
        menu = CRUD.create.cardapio(nome="M", tipo="t")
        prato = CRUD.create.prato(
            id_restaurante=rest.id, id_cardapio=menu.id,
            nome="Prato sem foto", slug="prato-sem-foto",
            preco_unidade=Decimal("10.00"), quantidade=5,
        )
        return rest.slug, prato.id


class PlaceholderTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.slug, self.prato_id = _seed_sem_imagem(self.app)
        self.client = self.app.test_client()

    def test_restaurant_without_image_gets_placeholder(self):
        r = self.client.get(f"/api/restaurantes/{self.slug}")
        self.assertEqual(r.status_code, 200, r.get_json())
        restaurante = r.get_json()["restaurante"]
        # Sem imagem própria => serve o placeholder padrão (não None).
        self.assertEqual(restaurante["imagem"], placeholders.PLACEHOLDER_URL)

    def test_dish_without_image_gets_placeholder(self):
        r = self.client.get(f"/api/restaurantes/{self.slug}")
        self.assertEqual(r.status_code, 200)
        pratos = r.get_json()["restaurante"]["pratos"]
        self.assertTrue(pratos)
        self.assertEqual(pratos[0]["imagem"], placeholders.PLACEHOLDER_URL)

    def test_placeholder_route_serves_png(self):
        r = self.client.get("/api/placeholder")
        self.assertEqual(r.status_code, 200)
        self.assertIn("image/png", r.headers.get("Content-Type", ""))
        # PNG começa com a assinatura \x89PNG.
        self.assertEqual(r.data[:4], b"\x89PNG")


if __name__ == "__main__":
    unittest.main()
