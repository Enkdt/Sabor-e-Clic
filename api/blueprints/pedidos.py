import logging
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from decorators import admin, customer, permission, validar
from extensions import db
from models.crud import CRUD
from models import services
from validations import check_json
from utils import err_json
import storage as _storage


pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# Minutos de preparo estimados por pedido. Fixo por ora; refinar quando houver dados de cozinha.
TEMPO_ESTIMADO_PADRAO = 30

# Fluxo do item após o cozinheiro confirmar (opção B: estado derivado do tempo decorrido).
# Total ~120s: metade até 'pronto', total até 'entregue'. Ajustável.
PREPARO_SEGUNDOS = 60
ENTREGA_SEGUNDOS = 120


def _status_efetivo_item(item):
    """Estado real do item: 'negado'/'aguardando' são fixos; após confirmado, deriva do tempo."""
    if item.status in ("negado", "aguardando"):
        return item.status
    # status armazenado é 'confirmado' (ou posterior); o tempo decorrido define o estágio atual.
    if item.confirmado_em is None:
        return item.status
    decorrido = (datetime.now(timezone.utc) - _aware(item.confirmado_em)).total_seconds()
    if decorrido >= ENTREGA_SEGUNDOS:
        return "entregue"
    if decorrido >= PREPARO_SEGUNDOS:
        return "pronto"
    return "preparando"


def _aware(dt):
    # confirmado_em é gravado em UTC; SQLite devolve naive — normaliza para comparar.
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _status_pedido(itens_efetivos):
    """Status agregado do pedido a partir dos estados efetivos dos itens."""
    ativos = [s for s in itens_efetivos if s != "negado"]
    if not ativos:
        return "negado"  # todos os itens negados
    if all(s == "entregue" for s in ativos):
        return "entregue"
    if any(s == "aguardando" for s in ativos):
        return "aguardando"
    if all(s in ("pronto", "entregue") for s in ativos):
        return "pronto"
    if any(s in ("preparando", "pronto", "confirmado", "entregue") for s in ativos):
        return "preparando"
    return "aguardando"


def _pedido_json(pedido):
    itens = []
    efetivos = []
    for item in pedido.associacao_prato:
        ef = _status_efetivo_item(item)
        efetivos.append(ef)
        itens.append({
            "id_prato": item.id_prato,
            "nome": item.prato.nome,
            "id_restaurante": item.prato.id_restaurante,
            "restaurante": item.prato.restaurante.nome,
            "restaurante_slug": item.prato.restaurante.slug,
            "imagem": _storage.url_for_key(item.prato.imagem) if item.prato.imagem else None,
            "quantidade": item.qtd,
            "preco_und": str(item.preco_und),
            "preco_total": str(item.preco_total),
            "status": ef,
            "motivo_negacao": item.motivo_negacao,
        })
    pago = pedido.status == "pago"
    return {
        "id": pedido.id,
        "data": pedido.data.isoformat(),
        "total": str(pedido.total),
        # 'status' do pedido: enquanto não pago, reflete o pagamento; depois, o andamento dos itens.
        "status": pedido.status if not pago else _status_pedido(efetivos),
        "pago": pago,
        "tempo_estimado": pedido.tempo_estimado,
        "metodo_pagamento": pedido.metodo_pagamento,
        "itens": itens,
    }


@pedidos_bp.post("/pedidos")
@validar
@permission(customer)
def criar_pedido():
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)

    itens = data.get("itens")
    if not isinstance(itens, list) or not itens:
        return err_json("VALIDATION_FAILED", "Informe ao menos um item no pedido.", status=400)

    # Resolve cada prato e calcula o total a partir do preço armazenado (nunca do cliente).
    linhas = []
    total = Decimal("0.00")
    for item in itens:
        if not isinstance(item, dict):
            return err_json("VALIDATION_FAILED", "Cada item deve conter id_prato e quantidade.", status=400)
        id_prato = item.get("id_prato")
        quantidade = item.get("quantidade")
        if type(id_prato) is not int or type(quantidade) is not int or quantidade <= 0:
            return err_json("VALIDATION_FAILED", "Informe id_prato e quantidade válidos.", status=400)
        prato = CRUD.read.prato(id_prato)
        if prato is None:
            return err_json("NOT_FOUND", f"Prato {id_prato} não encontrado.", status=404)
        # DATA-003: só pratos disponíveis podem ser pedidos.
        if not prato.disponivel:
            return err_json("DISH_UNAVAILABLE", f"O prato '{prato.nome}' está indisponível.", status=409)
        preco_und = Decimal(str(prato.preco_unidade))
        preco_total = (preco_und * quantidade).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += preco_total
        linhas.append((id_prato, quantidade, preco_und, preco_total))

    try:
        pedido = services.criar_pedido_com_itens(
            id_cliente=g.current_user.cliente.id_usuario,
            data=date.today(),
            total=total,
            status="preparando",
            tempo_estimado=TEMPO_ESTIMADO_PADRAO,
            linhas=linhas,
        )
    except SQLAlchemyError:
        # A transação já fez rollback no serviço: nada parcial é persistido.
        logger.exception("Falha ao criar pedido.")
        return err_json("DATABASE_ERROR", "Não foi possível criar o pedido.", status=500)

    return jsonify({"success": True, "pedido": _pedido_json(pedido)}), 201


@pedidos_bp.get("/pedidos")
@validar
@permission(customer)
def listar_pedidos():
    pedidos = CRUD.read.pedidos(filters={"id_cliente": g.current_user.cliente.id_usuario})
    pedidos = sorted(pedidos, key=lambda pedido: pedido.id, reverse=True)
    return jsonify({"pedidos": [_pedido_json(pedido) for pedido in pedidos]})


@pedidos_bp.get("/pedidos/<int:id>")
@validar
def obter_pedido(id):
    pedido = CRUD.read.pedido(id)
    if pedido is None:
        return err_json("NOT_FOUND", "Pedido não encontrado.", status=404)
    cliente = g.current_user.cliente
    dono = cliente is not None and pedido.id_cliente == cliente.id_usuario
    if not dono and g.current_role != admin:
        return err_json("PERMISSION_DENIED", "Você não tem permissão para acessar este pedido.", status=403)
    return jsonify({"pedido": _pedido_json(pedido)})


# Métodos de pagamento aceitos pelo placeholder MVP.
# shortcut: só "pagar na entrega"/"pix na entrega" por ora; trocar por gateway (Stripe/Mercado Pago/PIX) quando o produto decidir.
METODOS_PAGAMENTO = {"entrega", "pix_entrega"}


@pedidos_bp.post("/pedidos/<int:id>/pagamento")
@validar
@permission(customer)
def pagar_pedido(id):
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    metodo = data.get("metodo")
    if metodo not in METODOS_PAGAMENTO:
        return err_json("VALIDATION_FAILED", "Método de pagamento inválido.", status=400)

    pedido = CRUD.read.pedido(id)
    if pedido is None:
        return err_json("NOT_FOUND", "Pedido não encontrado.", status=404)
    if pedido.id_cliente != g.current_user.cliente.id_usuario:
        return err_json("PERMISSION_DENIED", "Você não tem permissão para pagar este pedido.", status=403)

    # Idempotente: pedido já pago não é cobrado de novo, apenas devolve o estado pago.
    if pedido.status == "pago":
        return jsonify({"success": True, "pedido": _pedido_json(pedido)})

    try:
        pedido = services.pagar_pedido(
            id_pedido=id,
            id_cliente=g.current_user.cliente.id_usuario,
            metodo=metodo,
            total=Decimal(str(pedido.total)),
        )
    except services.DomainError as error:
        if error.code == "ALREADY_PAID":
            # Corrida: outra requisição pagou primeiro. Idempotente.
            return jsonify({"success": True, "pedido": _pedido_json(CRUD.read.pedido(id))})
        return err_json(error.code, error.message, status=error.status)
    except SQLAlchemyError:
        logger.exception("Falha ao registrar pagamento do pedido %s.", id)
        return err_json("DATABASE_ERROR", "Não foi possível registrar o pagamento.", status=500)

    return jsonify({"success": True, "pedido": _pedido_json(pedido)})


def _avaliacao_json(avaliacao):
    return {
        "id": avaliacao.id,
        "id_pedido": avaliacao.id_pedido,
        "id_prato": avaliacao.id_prato,
        "prato": avaliacao.prato.nome,
        "id_restaurante": avaliacao.prato.id_restaurante,
        "restaurante": avaliacao.prato.restaurante.nome,
        "nota": avaliacao.nota,
        "comentario": avaliacao.comentario,
        "cliente": (avaliacao.cliente.usuario.nome if avaliacao.cliente and avaliacao.cliente.usuario else "Cliente"),
        "criado_em": avaliacao.criado_em.isoformat() if avaliacao.criado_em else None,
    }


def _pedido_do_cliente(id):
    """Carrega o pedido garantindo que pertence ao cliente autenticado. Retorna (pedido, erro)."""
    pedido = CRUD.read.pedido(id)
    if pedido is None:
        return None, err_json("NOT_FOUND", "Pedido não encontrado.", status=404)
    if pedido.id_cliente != g.current_user.cliente.id_usuario:
        return None, err_json("PERMISSION_DENIED", "Você não tem permissão para este pedido.", status=403)
    return pedido, None


@pedidos_bp.get("/pedidos/<int:id>/avaliacao")
@validar
@permission(customer)
def obter_avaliacao(id):
    pedido, erro = _pedido_do_cliente(id)
    if erro:
        return erro
    # Uma avaliação por prato do pedido; devolve a lista.
    existentes = CRUD.read.avaliacoes(filters={"id_pedido": id})
    return jsonify({"avaliacoes": [_avaliacao_json(a) for a in existentes]})


@pedidos_bp.post("/pedidos/<int:id>/avaliacao")
@validar
@permission(customer)
def criar_avaliacao(id):
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)

    pedido, erro = _pedido_do_cliente(id)
    if erro:
        return erro

    # Elegibilidade: só pedidos concluídos (estado terminal 'pago') podem ser avaliados.
    if pedido.status != "pago":
        return err_json("NOT_ELIGIBLE", "Só é possível avaliar pedidos concluídos.", status=409)

    id_prato = data.get("id_prato")
    if not isinstance(id_prato, int):
        return err_json("VALIDATION_FAILED", "Informe o id_prato a avaliar.", status=400)
    # O prato precisa pertencer a este pedido.
    item = next((i for i in pedido.associacao_prato if i.id_prato == id_prato), None)
    if item is None:
        return err_json("VALIDATION_FAILED", "Este prato não faz parte do pedido.", status=400)
    # SEC-005: elegibilidade por item — só o item efetivamente ENTREGUE pode ser
    # avaliado. Itens aguardando/confirmado/pronto/negado são recusados no servidor
    # (não confiar na visibilidade do front-end).
    if _status_efetivo_item(item) != "entregue":
        return err_json(
            "NOT_ELIGIBLE",
            "Só é possível avaliar um item após a entrega.",
            status=409,
        )

    nota = data.get("nota")
    if not isinstance(nota, int) or not (1 <= nota <= 5):
        return err_json("VALIDATION_FAILED", "A nota deve ser um inteiro entre 1 e 5.", status=400)
    comentario = data.get("comentario")
    if comentario is not None:
        if not isinstance(comentario, str) or len(comentario) > 500:
            return err_json("VALIDATION_FAILED", "Comentário inválido (máx. 500 caracteres).", status=400)
        comentario = comentario.strip() or None

    # Uma avaliação por prato dentro do pedido.
    if CRUD.read.avaliacoes(filters={"id_pedido": id, "id_prato": id_prato}, limit=1):
        return err_json("ALREADY_REVIEWED", "Este item já foi avaliado.", status=409)

    try:
        avaliacao = CRUD.create.avaliacao(
            id_pedido=id,
            id_prato=id_prato,
            id_cliente=g.current_user.cliente.id_usuario,
            nota=nota,
            comentario=comentario,
        )
    except IntegrityError:
        db.session.rollback()
        return err_json("ALREADY_REVIEWED", "Este item já foi avaliado.", status=409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao registrar avaliação do pedido %s.", id)
        return err_json("DATABASE_ERROR", "Não foi possível registrar a avaliação.", status=500)

    return jsonify({"success": True, "avaliacao": _avaliacao_json(avaliacao)}), 201
