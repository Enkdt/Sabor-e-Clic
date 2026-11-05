import logging
from datetime import datetime, timezone
from decimal import Decimal

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from decorators import admin, cook, permission, validar
from extensions import db
from models.crud import CRUD
from models.pedido import Pedido
from models.associacao import PedidoPrato
from validations import check_json
from utils import err_json
import storage

cozinha_bp = Blueprint("cozinha", __name__, url_prefix="/api/cozinha")
logger = logging.getLogger(__name__)


def _restaurantes_do_usuario():
    """IDs dos restaurantes que o usuário atual pode gerir (cozinheiro filiado; admin = todos)."""
    if g.current_role == "admin":
        return {r.id for r in CRUD.read.restaurantes()}
    if g.current_role == "cook" and g.current_user.cozinheiro:
        return {r.id for r in g.current_user.cozinheiro.restaurantes}
    return set()


def _item_json(item):
    return {
        "id_pedido": item.id_pedido,
        "id_prato": item.id_prato,
        "nome": item.prato.nome,
        "id_restaurante": item.prato.id_restaurante,
        "restaurante": item.prato.restaurante.nome,
        "imagem": storage.url_for_key(item.prato.imagem) if item.prato.imagem else None,
        "quantidade": item.qtd,
        "status": item.status,
        "motivo_negacao": item.motivo_negacao,
        "cliente": item.pedido.cliente.usuario.nome,
    }


@cozinha_bp.get("/pedidos")
@validar
@permission((cook, admin))
def listar_itens_cozinha():
    """Itens dos restaurantes do usuário que ainda não foram entregues/negados, do pedido pago."""
    meus = _restaurantes_do_usuario()
    if not meus:
        return jsonify({"itens": []})
    # Só itens de pedidos pagos (o fluxo da cozinha começa após o pagamento).
    itens = db.session.scalars(
        db.select(PedidoPrato).join(Pedido, PedidoPrato.id_pedido == Pedido.id).where(Pedido.status == "pago")
    ).all()
    visiveis = [
        i for i in itens
        if i.prato.id_restaurante in meus and i.status in ("aguardando", "confirmado")
    ]
    visiveis.sort(key=lambda i: (i.status != "aguardando", -i.id_pedido))
    return jsonify({"itens": [_item_json(i) for i in visiveis]})


def _carregar_item(id_pedido, id_prato):
    """Carrega o item garantindo que o usuário gere o restaurante dele. Retorna (item, erro)."""
    item = CRUD.read.pedido_prato((id_pedido, id_prato))
    if item is None:
        return None, err_json("NOT_FOUND", "Item do pedido não encontrado.", status=404)
    if item.prato.id_restaurante not in _restaurantes_do_usuario():
        return None, err_json("PERMISSION_DENIED", "Este item não é de um restaurante que você gerencia.", status=403)
    return item, None


@cozinha_bp.post("/itens/<int:id_pedido>/<int:id_prato>/confirmar")
@validar
@permission((cook, admin))
def confirmar_item(id_pedido, id_prato):
    item, erro = _carregar_item(id_pedido, id_prato)
    if erro:
        return erro
    if item.status != "aguardando":
        return err_json("INVALID_TRANSITION", f"Item não pode ser confirmado (estado atual: {item.status}).", status=409)
    try:
        CRUD.update.pedido_prato(
            (id_pedido, id_prato),
            {"status": "confirmado", "confirmado_em": datetime.now(timezone.utc)},
        )
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao confirmar item %s/%s.", id_pedido, id_prato)
        return err_json("DATABASE_ERROR", "Não foi possível confirmar o item.", status=500)
    return jsonify({"success": True, "item": _item_json(CRUD.read.pedido_prato((id_pedido, id_prato)))})


@cozinha_bp.post("/itens/<int:id_pedido>/<int:id_prato>/negar")
@validar
@permission((cook, admin))
def negar_item(id_pedido, id_prato):
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    motivo = data.get("motivo")
    motivo = motivo.strip() if isinstance(motivo, str) else ""
    if not motivo or len(motivo) > 200:
        return err_json("VALIDATION_FAILED", "Informe o motivo da recusa (até 200 caracteres).", status=400)

    item, erro = _carregar_item(id_pedido, id_prato)
    if erro:
        return erro
    # Só é possível negar antes de confirmar (não se já está em preparo/entregue).
    if item.status != "aguardando":
        return err_json("INVALID_TRANSITION", f"Item não pode ser negado (estado atual: {item.status}).", status=409)

    try:
        # Nega o item e estorna o valor dele ao saldo do cliente.
        cliente = item.pedido.cliente
        novo_saldo = Decimal(str(cliente.saldo)) + Decimal(str(item.preco_total))
        CRUD.update.cliente(cliente.id_usuario, {"saldo": novo_saldo})
        CRUD.update.pedido_prato((id_pedido, id_prato), {"status": "negado", "motivo_negacao": motivo})
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao negar item %s/%s.", id_pedido, id_prato)
        return err_json("DATABASE_ERROR", "Não foi possível negar o item.", status=500)
    return jsonify({"success": True, "item": _item_json(CRUD.read.pedido_prato((id_pedido, id_prato)))})
