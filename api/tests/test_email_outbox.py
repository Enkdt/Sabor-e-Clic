# MAIL-001: outbox durável de e-mail (enqueue + process com retry).
# Rodar: .venv/bin/python -m unittest tests.test_email_outbox

import logging
import tempfile
import unittest
from unittest import mock

from app import create_app
from models.crud import CRUD
from models import services  # noqa: F401 (garante import de serviços)
from models.email_service import enqueue_email, process_outbox, MAX_TENTATIVAS
from models.email_outbox import EmailOutbox
from extensions import db

logging.disable(logging.CRITICAL)


def _make_app():
    _, path = tempfile.mkstemp(suffix=".db")
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "RATELIMIT_ENABLED": False,
    })


class EmailOutboxTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()

    def test_enqueue_persists_pending(self):
        with self.app.app_context():
            enqueue_email("a@example.com", "Oi", "corpo")
            rows = db.session.execute(db.select(EmailOutbox)).scalars().all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].status, "pendente")
            self.assertEqual(rows[0].tentativas, 0)

    def test_process_sends_and_marks_sent(self):
        with self.app.app_context():
            enqueue_email("a@example.com", "Oi", "corpo", "<p>corpo</p>")
            with mock.patch("utils.sendEmail") as send:
                enviados, falhos = process_outbox()
            self.assertEqual((enviados, falhos), (1, 0))
            send.assert_called_once()
            row = db.session.execute(db.select(EmailOutbox)).scalars().one()
            self.assertEqual(row.status, "enviado")
            self.assertIsNotNone(row.enviado_em)

    def test_failure_increments_attempts_and_can_retry(self):
        with self.app.app_context():
            enqueue_email("a@example.com", "Oi", "corpo")
            with mock.patch("utils.sendEmail", side_effect=RuntimeError("smtp down")):
                process_outbox()
            row = db.session.execute(db.select(EmailOutbox)).scalars().one()
            self.assertEqual(row.status, "pendente")  # ainda pendente -> será reprocessado
            self.assertEqual(row.tentativas, 1)
            self.assertIn("smtp down", row.ultimo_erro)
            # Retry bem-sucedido.
            with mock.patch("utils.sendEmail") as send:
                process_outbox()
            send.assert_called_once()
            row = db.session.execute(db.select(EmailOutbox)).scalars().one()
            self.assertEqual(row.status, "enviado")

    def test_gives_up_after_max_attempts(self):
        with self.app.app_context():
            enqueue_email("a@example.com", "Oi", "corpo")
            with mock.patch("utils.sendEmail", side_effect=RuntimeError("down")):
                for _ in range(MAX_TENTATIVAS):
                    process_outbox()
            row = db.session.execute(db.select(EmailOutbox)).scalars().one()
            self.assertEqual(row.status, "falha")
            self.assertEqual(row.tentativas, MAX_TENTATIVAS)


class RegistrationStillSucceedsWhenEmailFailsTests(unittest.TestCase):
    def test_registration_201_even_if_smtp_fails(self):
        app = _make_app()
        client = app.test_client()
        payload = {
            "name": "Joao", "surname": "Silva", "email": "joao@example.com",
            "password": "Senha!Forte123", "password_confirmation": "Senha!Forte123",
            "cep": "01001-000", "country": "Brasil", "street": "Rua A", "number": "10",
            "neighborhood": "Centro", "city": "Sao Paulo", "state": "SP", "extra": "",
        }
        with mock.patch("utils.sendEmail", side_effect=RuntimeError("smtp down")):
            r = client.post("/api/cadastro", json=payload)
        self.assertEqual(r.status_code, 201, r.get_json())
        # O e-mail ficou registrado na outbox (pendente) para retry.
        with app.app_context():
            row = db.session.execute(db.select(EmailOutbox)).scalars().first()
            self.assertIsNotNone(row)
            self.assertEqual(row.destinatario, "joao@example.com")


if __name__ == "__main__":
    unittest.main()
