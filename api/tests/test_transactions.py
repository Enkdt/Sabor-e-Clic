# DATA-001 / DATA-002: atomicidade e concorrência das operações de negócio.
# Rodar: .venv/bin/python -m unittest tests.test_transactions

import logging
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

from app import create_app, db
from models.crud import CRUD
from models import services

logging.disable(logging.CRITICAL)

PASSWORD = "Senha!Forte123"


def _make_app():
    fd, path = tempfile.mkstemp(suffix=".db")
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "RATELIMIT_ENABLED": False,
    })


def _seed(app):
    with app.app_context():
        restaurante = CRUD.create.restaurante(nome="Cozinha Teste")
        menu = CRUD.create.cardapio(nome="Almoço", tipo="teste")
        prato = CRUD.create.prato(
            id_restaurante=restaurante.id, id_cardapio=menu.id,
            nome="Prato Feito", preco_unidade=Decimal("50.00"), quantidade=10,
        )
        user = CRUD.create.cliente_com_endereco(
            nome="Cliente Teste", email="cliente@example.com", senha=PASSWORD,
            rua="Rua A", numero="1", cep="01001-000", pais="Brasil",
            estado="SP", cidade="São Paulo", bairro="Centro",
        )
        CRUD.update.verificar_email(user.id)
        return prato.id, user.id


class OrderAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id, self.cliente_id = _seed(self.app)

    def test_order_creation_rolls_back_fully_on_line_failure(self):
        # Injeta falha ao criar a segunda linha: nenhum pedido deve persistir.
        from models import services as svc
        original_create = svc._create
        calls = {"n": 0}

        def flaky_create(model, data, **kwargs):
            from models.associacao import PedidoPrato
            if model is PedidoPrato:
                calls["n"] += 1
                if calls["n"] == 2:
                    raise RuntimeError("falha injetada na 2a linha")
            return original_create(model, data, **kwargs)

        with self.app.app_context():
            with mock.patch.object(svc, "_create", side_effect=flaky_create):
                with self.assertRaises(RuntimeError):
                    svc.criar_pedido_com_itens(
                        id_cliente=self.cliente_id,
                        data=__import__("datetime").date.today(),
                        total=Decimal("100.00"),
                        status="preparando",
                        tempo_estimado=30,
                        linhas=[
                            (self.prato_id, 1, Decimal("50.00"), Decimal("50.00")),
                            (self.prato_id, 1, Decimal("50.00"), Decimal("50.00")),
                        ],
                    )
            # Nenhum pedido órfão.
            self.assertEqual(len(CRUD.read.pedidos()), 0)


class PaymentConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id, self.cliente_id = _seed(self.app)
        with self.app.app_context():
            pedido = CRUD.create.pedido(
                id_cliente=self.cliente_id, data=__import__("datetime").date.today(),
                total=Decimal("50.00"), status="preparando", tempo_estimado=30,
            )
            self.pedido_id = pedido.id

    def test_double_payment_charges_once(self):
        with self.app.app_context():
            services.pagar_pedido(id_pedido=self.pedido_id, id_cliente=self.cliente_id,
                                  metodo="entrega", total=Decimal("50.00"))
            # Segunda tentativa deve ser idempotente (ALREADY_PAID), sem debitar de novo.
            with self.assertRaises(services.DomainError) as ctx:
                services.pagar_pedido(id_pedido=self.pedido_id, id_cliente=self.cliente_id,
                                      metodo="entrega", total=Decimal("50.00"))
            self.assertEqual(ctx.exception.code, "ALREADY_PAID")
            cliente = CRUD.read.cliente(self.cliente_id)
            # Saldo inicial 200 - 50 = 150 (cobrado exatamente uma vez).
            self.assertEqual(Decimal(str(cliente.saldo)), Decimal("150.00"))

    def test_payment_rejected_when_insufficient_funds(self):
        with self.app.app_context():
            # Zera o saldo via débito atômico direto.
            services._debitar_saldo(self.cliente_id, Decimal("200.00"))
            db.session.commit()
            with self.assertRaises(services.DomainError) as ctx:
                services.pagar_pedido(id_pedido=self.pedido_id, id_cliente=self.cliente_id,
                                      metodo="entrega", total=Decimal("50.00"))
            self.assertEqual(ctx.exception.code, "INSUFFICIENT_FUNDS")
            # Pedido NÃO foi marcado como pago (rollback).
            pedido = CRUD.read.pedido(self.pedido_id)
            self.assertNotEqual(pedido.status, "pago")


class AtomicBalanceTests(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.prato_id, self.cliente_id = _seed(self.app)

    def test_debit_predicate_blocks_overspend(self):
        with self.app.app_context():
            # Saldo 200. Débito de 250 deve falhar sem alterar o saldo.
            with self.assertRaises(services.DomainError):
                services._debitar_saldo(self.cliente_id, Decimal("250.00"))
            db.session.rollback()
            cliente = CRUD.read.cliente(self.cliente_id)
            self.assertEqual(Decimal(str(cliente.saldo)), Decimal("200.00"))


if __name__ == "__main__":
    unittest.main()
