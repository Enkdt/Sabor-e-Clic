"""Serviços de domínio transacionais e concorrência-seguros (DATA-001 / DATA-002).

Cada operação de negócio multi-entidade roda em UMA transação: ou todas as
gravações entram juntas, ou nenhuma. Reusa os helpers do CRUD com commit=False,
de modo que `models/crud.py` NÃO é reescrito — apenas ganhou um modo sem commit.

Concorrência (DATA-002):
- Débito/estorno de saldo usa UPDATE condicional atômico com predicado
  (`saldo >= :valor` no débito), evitando read-modify-write com leitura obsoleta.
  Isso é portável entre SQLite e PostgreSQL (uma linha afetada = sucesso).
- Transições de estado (pedido/agendamento/item) usam UPDATE condicional com
  predicado de status, garantindo que exatamente uma requisição concorrente
  vença (idempotência/estado esperado).
- Em dialetos que suportam (PostgreSQL), as leituras de linha usam
  `with_for_update()`; no SQLite o lock é no nível de transação.
"""
from contextlib import contextmanager
from decimal import Decimal

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from .crud import _create, _update_record, _delete_record, _EDITABLE
from .usuario import Cliente
from .pedido import Pedido
from .bancada import Agendamento
from .associacao import PedidoPrato


class DomainError(Exception):
    """Erro de regra de negócio (ex.: saldo insuficiente, transição inválida)."""

    def __init__(self, code, message, status=409):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@contextmanager
def _atomic():
    """Transação única para um caso de uso.

    Não usa db.session.begin() (a sessão com escopo do Flask-SQLAlchemy pode já
    ter uma transação implícita ativa). Faz commit ao final ou rollback em
    qualquer erro — os helpers do CRUD rodam com commit=False dentro deste bloco.
    """
    try:
        yield
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _debitar_saldo(id_cliente, valor: Decimal) -> None:
    """Débito atômico: só aplica se o saldo for suficiente. Falha => saldo insuficiente."""
    valor = Decimal(str(valor))
    resultado = db.session.execute(
        update(Cliente)
        .where(Cliente.id_usuario == id_cliente, Cliente.saldo >= valor)
        .values(saldo=Cliente.saldo - valor)
    )
    if resultado.rowcount != 1:
        raise DomainError("INSUFFICIENT_FUNDS", "Saldo insuficiente.", status=402)


def _creditar_saldo(id_cliente, valor: Decimal) -> None:
    """Crédito/estorno atômico (relativo, não sobrescreve valor absoluto)."""
    valor = Decimal(str(valor))
    db.session.execute(
        update(Cliente)
        .where(Cliente.id_usuario == id_cliente)
        .values(saldo=Cliente.saldo + valor)
    )


# ---------------------------------------------------------------------------
# Pedidos
# ---------------------------------------------------------------------------

def criar_pedido_com_itens(*, id_cliente, data, total, status, tempo_estimado, linhas):
    """Cria o pedido e todas as suas linhas em uma única transação.

    `linhas`: iterável de (id_prato, quantidade, preco_und, preco_total).
    Qualquer falha desfaz tudo (sem pedido órfão nem linhas parciais).
    """
    with _atomic():
        pedido = _create(Pedido, {
            "id_cliente": id_cliente,
            "data": data,
            "total": total,
            "status": status,
            "tempo_estimado": tempo_estimado,
        }, commit=False)
        for id_prato, quantidade, preco_und, preco_total in linhas:
            _create(PedidoPrato, {
                "id_pedido": pedido.id,
                "id_prato": id_prato,
                "qtd": quantidade,
                "preco_und": preco_und,
                "preco_total": preco_total,
            }, commit=False)
    return pedido


def pagar_pedido(*, id_pedido, id_cliente, metodo, total):
    """Debita o saldo e marca o pedido como pago atomicamente e sob concorrência.

    Usa UPDATE condicional no status (só de != 'pago' para 'pago') para impedir
    pagamento duplo, e débito atômico com predicado de saldo.
    """
    total = Decimal(str(total))
    with _atomic():
        # Transição de estado condicional: vence exatamente uma requisição.
        marcado = db.session.execute(
            update(Pedido)
            .where(Pedido.id == id_pedido, Pedido.status != "pago")
            .values(status="pago", metodo_pagamento=metodo)
        )
        if marcado.rowcount != 1:
            # Já estava pago (ou não existe): idempotente, sem cobrança.
            raise DomainError("ALREADY_PAID", "Pedido já pago.", status=200)
        _debitar_saldo(id_cliente, total)
    return db.session.get(Pedido, id_pedido)


# ---------------------------------------------------------------------------
# Agendamentos de bancada
# ---------------------------------------------------------------------------

def criar_agendamento_com_debito(*, id_cliente, id_bancada, horario, duracao, preco):
    """Cria o agendamento 'pendente' e debita o saldo em uma transação."""
    preco = Decimal(str(preco))
    with _atomic():
        _debitar_saldo(id_cliente, preco)
        agendamento = _create(Agendamento, {
            "id_cliente": id_cliente,
            "id_bancada": id_bancada,
            "horario_agendado": horario,
            "tempo_agendado": duracao,
            "preco_total": preco,
            "status": "pendente",
        }, commit=False)
    return agendamento


def aceitar_agendamento(*, ag_id):
    """Aceita apenas se ainda estiver 'pendente' (transição condicional)."""
    with _atomic():
        marcado = db.session.execute(
            update(Agendamento)
            .where(Agendamento.id == ag_id, Agendamento.status == "pendente")
            .values(status="aceito")
        )
        if marcado.rowcount != 1:
            raise DomainError("INVALID_TRANSITION", "Agendamento não está pendente.", status=409)
        # Revalida sobreposição com outros ACEITOS já dentro da transação.
        ag = db.session.get(Agendamento, ag_id)
        from .crud import _ensure_booking_available
        _ensure_booking_available(
            {
                "id_bancada": ag.id_bancada,
                "horario_agendado": ag.horario_agendado,
                "tempo_agendado": ag.tempo_agendado,
                "status": "aceito",
            },
            exclude_id=ag.id,
        )
    return db.session.get(Agendamento, ag_id)


def negar_agendamento(*, ag_id, motivo):
    """Nega (de 'pendente') e estorna o saldo em uma transação, sem estorno duplo."""
    with _atomic():
        ag = db.session.get(Agendamento, ag_id)
        if ag is None:
            raise DomainError("NOT_FOUND", "Agendamento não encontrado.", status=404)
        marcado = db.session.execute(
            update(Agendamento)
            .where(Agendamento.id == ag_id, Agendamento.status == "pendente")
            .values(status="negado", motivo_negacao=motivo)
        )
        if marcado.rowcount != 1:
            raise DomainError("INVALID_TRANSITION", "Agendamento não está pendente.", status=409)
        if ag.id_cliente is not None:
            _creditar_saldo(ag.id_cliente, Decimal(str(ag.preco_total)))
    return db.session.get(Agendamento, ag_id)


# ---------------------------------------------------------------------------
# Itens de pedido (cozinha)
# ---------------------------------------------------------------------------

def negar_item(*, id_pedido, id_prato, motivo):
    """Nega o item (de 'aguardando') e estorna seu valor ao cliente, atomicamente."""
    with _atomic():
        item = db.session.get(PedidoPrato, (id_pedido, id_prato))
        if item is None:
            raise DomainError("NOT_FOUND", "Item não encontrado.", status=404)
        marcado = db.session.execute(
            update(PedidoPrato)
            .where(
                PedidoPrato.id_pedido == id_pedido,
                PedidoPrato.id_prato == id_prato,
                PedidoPrato.status == "aguardando",
            )
            .values(status="negado", motivo_negacao=motivo)
        )
        if marcado.rowcount != 1:
            raise DomainError("INVALID_TRANSITION", "Item não pode ser negado.", status=409)
        cliente = item.pedido.cliente
        if cliente is not None:
            _creditar_saldo(cliente.id_usuario, Decimal(str(item.preco_total)))
    return db.session.get(PedidoPrato, (id_pedido, id_prato))
