import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, request

from decorators import admin, permission, validar
from extensions import db
from models.pedido import Pedido
from models.restaurante import Ingrediente

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

    pedidos = db.session.scalars(
        db.select(Pedido).where(Pedido.data >= inicio)
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
