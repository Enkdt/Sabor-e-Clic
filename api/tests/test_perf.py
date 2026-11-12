# PERF-001: a listagem da cozinha usa um número de queries LIMITADO (sem N+1),
# independente da quantidade de itens. Mede contando execuções no engine.
# Rodar: .venv/bin/python -m unittest tests.test_perf

import logging
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from sqlalchemy import event

from app import create_app, db
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


def _seed(app, n_itens):
    with app.app_context():
        rest = CRUD.create.restaurante(nome="Resto", slug="resto")
        menu = CRUD.create.cardapio(nome="M", tipo="t")
        cook = CRUD.create.cozinheiro(nome="Cook", email="cook@example.com", senha=PASSWORD, especialidade="g")
        CRUD.update.verificar_email(cook.id_usuario)
        CRUD.create.cozinheiro_restaurante(cook.id_usuario, rest.id)
        cliente = CRUD.create.cliente_com_endereco(
            nome="Ana", email="ana@example.com", senha=PASSWORD,
            rua="R", numero="1", cep="01001-000", pais="BR", estado="SP", cidade="SP", bairro="C",
        )
        CRUD.update.verificar_email(cliente.id)
        pratos = [
            CRUD.create.prato(id_restaurante=rest.id, id_cardapio=menu.id, nome=f"P{i}",
                              slug=f"p{i}", preco_unidade=Decimal("10.00"), quantidade=5)
            for i in range(n_itens)
        ]
        pedido = CRUD.create.pedido(id_cliente=cliente.id, data=date.today(),
                                    total=Decimal("10.00"), status="pago", tempo_estimado=30)
        for p in pratos:
            CRUD.create.pedido_prato(id_pedido=pedido.id, id_prato=p.id, qtd=1,
                                     preco_und=Decimal("10.00"), preco_total=Decimal("10.00"))


class QueryCountTests(unittest.TestCase):
    def _count_for(self, n_itens):
        app = _make_app()
        _seed(app, n_itens)
        client = app.test_client()
        client.post("/api/login", json={"email": "cook@example.com", "password": PASSWORD})
        count = {"n": 0}

        def _before(conn, cursor, statement, params, context, executemany):
            count["n"] += 1

        with app.app_context():
            engine = db.engine
        event.listen(engine, "before_cursor_execute", _before)
        try:
            r = client.get("/api/cozinha/pedidos")
            self.assertEqual(r.status_code, 200, r.get_json())
            self.assertEqual(len(r.get_json()["itens"]), n_itens)
        finally:
            event.remove(engine, "before_cursor_execute", _before)
        return count["n"]

    def test_query_count_does_not_grow_with_items(self):
        poucos = self._count_for(2)
        muitos = self._count_for(20)
        # Sem N+1: a contagem de queries da listagem não deve crescer com o número
        # de itens. Tolerância pequena para variação de sessão/login.
        self.assertLessEqual(muitos, poucos + 2,
                             f"consultas cresceram com os itens: {poucos} -> {muitos}")


if __name__ == "__main__":
    unittest.main()
