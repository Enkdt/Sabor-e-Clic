import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from decorators import admin, cook, permission, validar
from extensions import db
from models.crud import CRUD
from validations import check_json
from utils import err_json
import storage

estoque_bp = Blueprint("estoque", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# Unidades aceitas. shortcut: lista fixa no app; mover para tabela/constraint se o produto exigir.
UNIDADES = {"kg", "g", "L", "mL", "un"}


def _ingrediente_json(ing):
    return {
        "id": ing.id,
        "nome": ing.nome,
        "validade": ing.validade.isoformat(),
        "unidade": ing.unidade,
        "quantidade": str(ing.quantidade),
        "imagem": storage.url_for_key(ing.imagem) if ing.imagem else None,
    }


def _parse_ingrediente(data, *, partial=False):
    """Valida e normaliza os campos do ingrediente. Retorna (valores, erros)."""
    errors = {}
    values = {}

    if not partial or "nome" in data:
        nome = data.get("nome")
        nome = nome.strip() if isinstance(nome, str) else ""
        if not nome:
            errors["nome"] = "Informe o nome do produto."
        elif len(nome) > 30:
            errors["nome"] = "O nome deve ter no máximo 30 caracteres."
        else:
            values["nome"] = nome

    if not partial or "validade" in data:
        raw = data.get("validade")
        try:
            values["validade"] = date.fromisoformat(raw) if isinstance(raw, str) else None
            if values["validade"] is None:
                raise ValueError
        except (ValueError, TypeError):
            errors["validade"] = "Informe uma data de validade válida (AAAA-MM-DD)."

    if not partial or "unidade" in data:
        unidade = data.get("unidade")
        if unidade not in UNIDADES:
            errors["unidade"] = f"Unidade inválida. Use uma de: {', '.join(sorted(UNIDADES))}."
        else:
            values["unidade"] = unidade

    if not partial or "quantidade" in data:
        try:
            quantidade = Decimal(str(data.get("quantidade")))
            if quantidade < 0:
                errors["quantidade"] = "A quantidade não pode ser negativa."
            else:
                values["quantidade"] = quantidade
        except (InvalidOperation, TypeError, ValueError):
            errors["quantidade"] = "Informe uma quantidade numérica válida."

    # Imagem é opcional: chave devolvida por POST /api/uploads, ou null para remover.
    if "imagem" in data:
        imagem = data.get("imagem")
        if imagem is None:
            values["imagem"] = None
        elif isinstance(imagem, str) and imagem.strip():
            values["imagem"] = imagem.strip()
        else:
            errors["imagem"] = "Imagem inválida."

    return values, errors


@estoque_bp.get("/ingredientes")
@validar
@permission((cook, admin))
def listar_ingredientes():
    ingredientes = CRUD.read.ingredientes()
    ingredientes = sorted(ingredientes, key=lambda i: i.nome.lower())
    return jsonify({"ingredientes": [_ingrediente_json(i) for i in ingredientes]})


@estoque_bp.post("/ingredientes")
@validar
@permission(admin)
def criar_ingrediente():
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    values, errors = _parse_ingrediente(data)
    if errors:
        return err_json("VALIDATION_FAILED", "Preencha os campos corretamente.", fields=errors, status=400)
    try:
        ingrediente = CRUD.create.ingrediente(**values)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao criar ingrediente.")
        return err_json("DATABASE_ERROR", "Não foi possível salvar o item.", status=500)
    return jsonify({"success": True, "ingrediente": _ingrediente_json(ingrediente)}), 201


@estoque_bp.patch("/ingredientes/<int:id>")
@validar
@permission(admin)
def atualizar_ingrediente(id):
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    values, errors = _parse_ingrediente(data, partial=True)
    if errors:
        return err_json("VALIDATION_FAILED", "Preencha os campos corretamente.", fields=errors, status=400)
    if not values:
        return err_json("VALIDATION_FAILED", "Informe ao menos um campo para atualizar.", status=400)
    try:
        ingrediente = CRUD.update.ingrediente(id, values)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao atualizar ingrediente %s.", id)
        return err_json("DATABASE_ERROR", "Não foi possível atualizar o item.", status=500)
    if ingrediente is None:
        return err_json("NOT_FOUND", "Item não encontrado.", status=404)
    return jsonify({"success": True, "ingrediente": _ingrediente_json(ingrediente)})
