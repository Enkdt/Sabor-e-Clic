import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, g, jsonify, request

from decorators import admin, cook, permission, validar
from extensions import db
from models.pedido import Pedido
from models.associacao import PedidoPrato
from models.restaurante import Ingrediente
from utils import err_json

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# Períodos aceitos pelo filtro (em dias). Único filtro com dado de verdade por trás.
# shortcut: região/categoria não têm campo no domínio; o frontend os desabilita até existir dado.
PERIODOS = {"7": 7, "30": 30, "90": 90}
WEEKDAY_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def _money(value):
    return str(Decimal(value).quantize(Decimal("0.01")))


@dashboard_bp.get("/dashboard")
@validar
@permission(admin)
def metricas():
    dias = PERIODOS.get(str(request.args.get("periodo", "30")), 30)
    inicio = date.today() - timedelta(days=dias)

    # PERF-001: eager-load das linhas e seus pratos/restaurantes usados na agregação
    # por restaurante (evita N+1 ao percorrer p.associacao_prato[].prato.restaurante).
    from sqlalchemy.orm import joinedload, selectinload
    from models.restaurante import Prato
    pedidos = db.session.scalars(
        db.select(Pedido)
        .where(Pedido.data >= inicio)
        .options(selectinload(Pedido.associacao_prato).joinedload(PedidoPrato.prato).joinedload(Prato.restaurante))
    ).all()

    pagos = [p for p in pedidos if p.status == "pago"]
    receita = sum((Decimal(str(p.total)) for p in pagos), Decimal("0.00"))
    ticket_medio = (receita / len(pagos)) if pagos else Decimal("0.00")

    # Vendas por dia da semana (todos os pedidos no período).
    por_dia = defaultdict(int)
    for p in pedidos:
        por_dia[p.data.weekday()] += 1
    vendas_por_dia = [{"label": WEEKDAY_LABELS[i], "value": por_dia.get(i, 0)} for i in range(7)]

    # Receita por restaurante (pedidos pagos), derivada das linhas de pedido.
    por_restaurante = defaultdict(Decimal)
    for p in pagos:
        for linha in p.associacao_prato:
            restaurante = linha.prato.restaurante if linha.prato else None
            nome = restaurante.nome if restaurante else "—"
            por_restaurante[nome] += Decimal(str(linha.preco_total))
    receita_por_restaurante = [
        {"label": nome, "value": _money(valor)}
        for nome, valor in sorted(por_restaurante.items(), key=lambda kv: kv[1], reverse=True)
    ]

    ingredientes = db.session.scalars(db.select(Ingrediente)).all()
    sem_estoque = sum(1 for i in ingredientes if Decimal(str(i.quantidade)) <= 0)

    return jsonify({
        "periodo": {"dias": dias, "inicio": inicio.isoformat(), "fim": date.today().isoformat()},
        "kpis": {
            "receita_total": _money(receita),
            "pedidos_pagos": len(pagos),
            "pedidos_total": len(pedidos),
            "ticket_medio": _money(ticket_medio),
            "itens_estoque": len(ingredientes),
            "itens_sem_estoque": sem_estoque,
        },
        "vendas_por_dia": vendas_por_dia,
        "receita_por_restaurante": receita_por_restaurante,
    })


def _pode_ver_restaurante(id_restaurante):
    """Admin vê qualquer restaurante; cozinheiro só os que gerencia."""
    if g.current_role == "admin":
        return True
    cozinheiro = getattr(g.current_user, "cozinheiro", None)
    if cozinheiro is None:
        return False
    return any(r.id == id_restaurante for r in cozinheiro.restaurantes)


@dashboard_bp.get("/restaurantes/<int:id_restaurante>/metricas")
@validar
@permission((cook, admin))
def metricas_restaurante(id_restaurante):
    """Mini dashboard por restaurante: KPIs escopados aos pratos deste restaurante.

    Receita/ticket consideram apenas as LINHAS de pedidos pagos cujo prato pertence
    ao restaurante (não o total do pedido, que pode misturar restaurantes).
    """
    from models.restaurante import Prato, Restaurante
    restaurante = db.session.get(Restaurante, id_restaurante)
    if restaurante is None:
        return err_json("NOT_FOUND", "Restaurante não encontrado.", status=404)
    if not _pode_ver_restaurante(id_restaurante):
        return err_json("PERMISSION_DENIED", "Você não gerencia este restaurante.", status=403)

    dias = PERIODOS.get(str(request.args.get("periodo", "30")), 30)
    inicio = date.today() - timedelta(days=dias)

    from sqlalchemy.orm import joinedload, selectinload
    pedidos = db.session.scalars(
        db.select(Pedido)
        .where(Pedido.data >= inicio, Pedido.status == "pago")
        .options(selectinload(Pedido.associacao_prato).joinedload(PedidoPrato.prato))
    ).all()

    receita = Decimal("0.00")
    pedidos_com_restaurante = 0
    itens_vendidos = 0
    por_dia = defaultdict(int)
    por_prato = defaultdict(Decimal)
    for p in pedidos:
        linhas_do_restaurante = [
            l for l in p.associacao_prato
            if l.prato is not None and l.prato.id_restaurante == id_restaurante
        ]
        if not linhas_do_restaurante:
            continue
        pedidos_com_restaurante += 1
        por_dia[p.data.weekday()] += 1
        for l in linhas_do_restaurante:
            receita += Decimal(str(l.preco_total))
            itens_vendidos += l.qtd
            por_prato[l.prato.nome] += Decimal(str(l.preco_total))

    ticket_medio = (receita / pedidos_com_restaurante) if pedidos_com_restaurante else Decimal("0.00")
    vendas_por_dia = [{"label": WEEKDAY_LABELS[i], "value": por_dia.get(i, 0)} for i in range(7)]
    receita_por_prato = [
        {"label": nome, "value": _money(valor)}
        for nome, valor in sorted(por_prato.items(), key=lambda kv: kv[1], reverse=True)
    ]
    pratos_do_restaurante = db.session.scalars(
        db.select(Prato).where(Prato.id_restaurante == id_restaurante)
    ).all()
    pratos_indisponiveis = sum(1 for pr in pratos_do_restaurante if not pr.disponivel)

    return jsonify({
        "restaurante": {"id": restaurante.id, "nome": restaurante.nome, "slug": restaurante.slug},
        "periodo": {"dias": dias, "inicio": inicio.isoformat(), "fim": date.today().isoformat()},
        "kpis": {
            "receita_total": _money(receita),
            "pedidos_pagos": pedidos_com_restaurante,
            "itens_vendidos": itens_vendidos,
            "ticket_medio": _money(ticket_medio),
            "pratos_total": len(pratos_do_restaurante),
            "pratos_indisponiveis": pratos_indisponiveis,
        },
        "vendas_por_dia": vendas_por_dia,
        "receita_por_prato": receita_por_prato,
    })
