# Testes de upload de imagem (C8) — validação por magic bytes, auth, e associação a entidades.
# Rodar: .venv/bin/python -m unittest tests.test_uploads

import io
import logging
import tempfile
import unittest

from app import create_app
from models.crud import CRUD

logging.disable(logging.CRITICAL)

PASSWORD = "Senha!Forte123"

# PNG mínimo válido (assinatura + resto do arquivo 1x1).
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f5f0000000049454e44ae426082"
)


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
        admin = CRUD.create.funcionario(nome="Admin", email="admin@example.com", senha=PASSWORD, nivel_permissao=5)
        CRUD.update.verificar_email(admin.id_usuario)
        cliente = CRUD.create.cliente_com_endereco(
            nome="Cliente", email="cliente@example.com", senha=PASSWORD,
            rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
        )
        CRUD.update.verificar_email(cliente.id)
        restaurante = CRUD.create.restaurante(nome="Resto")
        menu = CRUD.create.cardapio(nome="M", tipo="t")
        prato = CRUD.create.prato(id_restaurante=restaurante.id, id_cardapio=menu.id, nome="P", preco_unidade=10, quantidade=5)
        return restaurante.id, prato.id


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.rest_id, self.prato_id = _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def _upload_png(self):
        return self.client.post(
            "/api/uploads",
            data={"file": (io.BytesIO(PNG_BYTES), "foto.png")},
            content_type="multipart/form-data",
        )

    def test_upload_requires_auth(self):
        response = self._upload_png()
        self.assertEqual(response.status_code, 401)

    def test_upload_valid_png_and_serve(self):
        self._login("cliente@example.com")
        response = self._upload_png()
        self.assertEqual(response.status_code, 201, response.get_json())
        url = response.get_json()["url"]
        self.assertTrue(url.startswith("/api/uploads/"))
        served = self.client.get(url)
        self.assertEqual(served.status_code, 200)

    def test_upload_rejects_non_image(self):
        self._login("cliente@example.com")
        response = self.client.post(
            "/api/uploads",
            data={"file": (io.BytesIO(b"not an image"), "x.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400, response.get_json())

    def test_admin_sets_restaurant_and_dish_image(self):
        self._login("admin@example.com")
        key = self._upload_png().get_json()["key"]
        r = self.client.patch(f"/api/restaurantes/{self.rest_id}/imagem", json={"imagem": key})
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertTrue(r.get_json()["restaurante"]["imagem"].endswith(key))
        p = self.client.patch(f"/api/pratos/{self.prato_id}/imagem", json={"imagem": key})
        self.assertEqual(p.status_code, 200, p.get_json())
        self.assertTrue(p.get_json()["prato"]["imagem"].endswith(key))

    def test_customer_cannot_set_restaurant_image(self):
        self._login("cliente@example.com")
        key = self._upload_png().get_json()["key"]
        r = self.client.patch(f"/api/restaurantes/{self.rest_id}/imagem", json={"imagem": key})
        self.assertEqual(r.status_code, 403, r.get_json())

    def test_customer_sets_own_avatar(self):
        self._login("cliente@example.com")
        key = self._upload_png().get_json()["key"]
        a = self.client.patch("/api/perfil/avatar", json={"avatar": key})
        self.assertEqual(a.status_code, 200, a.get_json())
        self.assertTrue(a.get_json()["avatar"].endswith(key))


if __name__ == "__main__":
    unittest.main()
