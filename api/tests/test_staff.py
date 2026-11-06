# Testes de criação de contas de staff (Ticket 8). Admin-only.
# Rodar: .venv/bin/python -m unittest test_staff
#

import logging
import tempfile
import unittest

from app import create_app
from models.crud import CRUD

logging.disable(logging.CRITICAL)

PASSWORD = "Senha!Forte123"
STAFF_PASSWORD = "C0zinh@Segura!99"


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
        cliente = CRUD.create.cliente_com_endereco(
            nome="Cliente", email="cliente@example.com", senha=PASSWORD,
            rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="Centro",
        )
        CRUD.update.verificar_email(cliente.id)


class StaffTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email, password=PASSWORD):
        return self.client.post("/api/login", json={"email": email, "password": password})

    def test_admin_creates_cook_who_can_login(self):
        self._login("admin@example.com")
        created = self.client.post("/api/usuarios/staff", json={
            "role": "cook", "nome": "Rafael", "email": "rafael@example.com",
            "password": STAFF_PASSWORD, "especialidade": "Vegana",
        })
        self.assertEqual(created.status_code, 201, created.get_json())
        self.client.post("/api/logout")
        login = self._login("rafael@example.com", STAFF_PASSWORD)
        self.assertEqual(login.status_code, 200, login.get_json())
        self.assertEqual(login.get_json()["user"]["role"], "cook")

    def test_admin_creates_admin(self):
        self._login("admin@example.com")
        created = self.client.post("/api/usuarios/staff", json={
            "role": "admin", "nome": "Nova", "email": "nova.admin@example.com",
            "password": STAFF_PASSWORD, "nivel_permissao": 3,
        })
        self.assertEqual(created.status_code, 201, created.get_json())

    def test_invalid_role_rejected(self):
        self._login("admin@example.com")
        response = self.client.post("/api/usuarios/staff", json={
            "role": "superuser", "nome": "X", "email": "x@example.com", "password": STAFF_PASSWORD,
        })
        self.assertEqual(response.status_code, 400, response.get_json())

    def test_duplicate_email_rejected(self):
        self._login("admin@example.com")
        response = self.client.post("/api/usuarios/staff", json={
            "role": "cook", "nome": "Dup", "email": "cliente@example.com",
            "password": STAFF_PASSWORD, "especialidade": "X",
        })
        self.assertEqual(response.status_code, 409, response.get_json())

    def test_weak_password_rejected(self):
        self._login("admin@example.com")
        response = self.client.post("/api/usuarios/staff", json={
            "role": "cook", "nome": "Weak", "email": "weak@example.com",
            "password": "123", "especialidade": "X",
        })
        self.assertEqual(response.status_code, 400, response.get_json())

    def test_non_admin_forbidden(self):
        self._login("cliente@example.com")
        response = self.client.post("/api/usuarios/staff", json={
            "role": "cook", "nome": "X", "email": "x@example.com",
            "password": STAFF_PASSWORD, "especialidade": "X",
        })
        self.assertEqual(response.status_code, 403, response.get_json())

    def test_requires_authentication(self):
        response = self.client.post("/api/usuarios/staff", json={
            "role": "cook", "nome": "X", "email": "x@example.com",
            "password": STAFF_PASSWORD, "especialidade": "X",
        })
        self.assertEqual(response.status_code, 401, response.get_json())


if __name__ == "__main__":
    unittest.main()
