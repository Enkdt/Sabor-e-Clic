# Testes do fluxo de bancada: cliente pede → cozinheiro/admin aceita/nega → aceito ocupa o horário.
# Rodar: .venv/bin/python -m unittest tests.test_bancadas

import logging
import tempfile
import unittest
from datetime import date, datetime, time, timedelta
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


def _amanha(hora, minuto=0):
    d = date.today() + timedelta(days=1)
    return datetime(d.year, d.month, d.day, hora, minuto).isoformat(timespec="minutes")


def _seed(app):
    with app.app_context():
        admin = CRUD.create.funcionario(nome="Admin", email="admin@example.com", senha=PASSWORD, nivel_permissao=5)
        CRUD.update.verificar_email(admin.id_usuario)
        cook = CRUD.create.cozinheiro(nome="Rafa", email="rafa@example.com", senha=PASSWORD, especialidade="geral")
        CRUD.update.verificar_email(cook.id_usuario)
        rest = CRUD.create.restaurante(nome="Resto", slug="resto")
        CRUD.create.cozinheiro_restaurante(cook.id_usuario, rest.id)  # cozinheiro vinculado
        for email in ("ana@example.com", "bruno@example.com"):
            c = CRUD.create.cliente_com_endereco(
                nome="C", email=email, senha=PASSWORD,
                rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
            )
            CRUD.update.verificar_email(c.id)
        bancada = CRUD.create.bancada(preco_hora=Decimal("60.00"))
        CRUD.create.bancada_endereco(id_bancada=bancada.id, id=1, rua="R", numero="1", complemento="Bancada A", bairro="C", cidade="SP", estado="SP")
        CRUD.create.bancada_horario_disponivel(id_bancada=bancada.id, id=1, inicio=time(8, 0), fim=time(18, 0))
        return bancada.id


class BancadaTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.bancada_id = _seed(self.app)
        self.client = self.app.test_client()

    def _login(self, email):
        self.client.post("/api/login", json={"email": email, "password": PASSWORD})

    def _pedir(self, inicio, fim):
        return self.client.post(f"/api/bancadas/{self.bancada_id}/agendamentos", json={"inicio": inicio, "fim": fim})

    def test_client_requests_and_saldo_debited(self):
        self._login("ana@example.com")
        r = self._pedir(_amanha(10), _amanha(11))  # 1h × 60 = 60
        self.assertEqual(r.status_code, 201, r.get_json())
        self.assertEqual(r.get_json()["agendamento"]["status"], "pendente")
        with self.app.app_context():
            self.assertEqual(str(CRUD.read.usuario_por_email("ana@example.com").cliente.saldo), "140.00")

    def test_cook_not_customer_cannot_request(self):
        self._login("rafa@example.com")
        r = self._pedir(_amanha(10), _amanha(11))
        self.assertEqual(r.status_code, 403, r.get_json())

    def test_accept_then_blocks_overlap(self):
        self._login("ana@example.com")
        ag_id = self._pedir(_amanha(10), _amanha(12)).get_json()["agendamento"]["id"]
        self.client.post("/api/logout")
        self._login("rafa@example.com")
        ac = self.client.post(f"/api/bancadas/agendamentos/{ag_id}/aceitar")
        self.assertEqual(ac.status_code, 200, ac.get_json())
        self.assertEqual(ac.get_json()["agendamento"]["status"], "aceito")
        # Outro cliente tenta um horário sobreposto -> conflito.
        self.client.post("/api/logout")
        self._login("bruno@example.com")
        conflito = self._pedir(_amanha(11), _amanha(13))
        self.assertEqual(conflito.status_code, 409, conflito.get_json())

    def test_deny_refunds_saldo(self):
        self._login("ana@example.com")
        with self.app.app_context():
            antes = Decimal(str(CRUD.read.usuario_por_email("ana@example.com").cliente.saldo))
        ag_id = self._pedir(_amanha(14), _amanha(15)).get_json()["agendamento"]["id"]
        self.client.post("/api/logout")
        self._login("rafa@example.com")
        dn = self.client.post(f"/api/bancadas/agendamentos/{ag_id}/negar", json={"motivo": "Indisponível"})
        self.assertEqual(dn.status_code, 200, dn.get_json())
        self.assertEqual(dn.get_json()["agendamento"]["status"], "negado")
        with self.app.app_context():
            self.assertEqual(Decimal(str(CRUD.read.usuario_por_email("ana@example.com").cliente.saldo)), antes)

    def test_pending_does_not_block(self):
        # Dois pedidos pendentes no mesmo horário são permitidos (pendente não ocupa).
        self._login("ana@example.com")
        self.assertEqual(self._pedir(_amanha(9), _amanha(10)).status_code, 201)
        self.client.post("/api/logout")
        self._login("bruno@example.com")
        self.assertEqual(self._pedir(_amanha(9), _amanha(10)).status_code, 201)

    def test_occupied_slot_shown(self):
        self._login("ana@example.com")
        ag_id = self._pedir(_amanha(16), _amanha(17)).get_json()["agendamento"]["id"]
        self.client.post("/api/logout")
        self._login("rafa@example.com")
        self.client.post(f"/api/bancadas/agendamentos/{ag_id}/aceitar")
        got = self.client.get(f"/api/bancadas/{self.bancada_id}")
        self.assertEqual(len(got.get_json()["bancada"]["ocupados"]), 1)

    def test_insufficient_funds(self):
        self._login("ana@example.com")
        with self.app.app_context():
            ana = CRUD.read.usuario_por_email("ana@example.com").cliente
            CRUD.update.cliente(ana.id_usuario, {"saldo": Decimal("0.00")})
        r = self._pedir(_amanha(10), _amanha(11))
        self.assertEqual(r.status_code, 402, r.get_json())


if __name__ == "__main__":
    unittest.main()
