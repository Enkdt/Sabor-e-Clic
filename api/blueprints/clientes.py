import logging
from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from decorators import customer, permission, validar
from extensions import db
from models.crud import CRUD
from validations import check_json
from utils import err_json
import storage

clientes_bp = Blueprint("clientes", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


def _endereco_json(endereco):
    return {
        "id": endereco.id,
        "rua": endereco.rua,
        "numero": endereco.numero,
        "complemento": endereco.complemento,
        "cep": endereco.cep,
        "bairro": endereco.bairro,
        "cidade": endereco.cidade,
        "estado": endereco.estado,
        "pais": endereco.pais,
    }


@clientes_bp.get("/enderecos")
@validar
@permission(customer)
def listar_enderecos():
    """Endereços do cliente autenticado (o mais antigo é tratado como padrão de entrega)."""
    enderecos = CRUD.read.enderecos_cliente(
        filters={"id_usuario": g.current_user.cliente.id_usuario}
    )
    return jsonify({"enderecos": [_endereco_json(item) for item in enderecos]})


@clientes_bp.get("/perfil/avatar")
@validar
@permission(customer)
def obter_avatar():
    cliente = g.current_user.cliente
    return jsonify({"avatar": storage.url_for_key(cliente.avatar) if cliente.avatar else None})


@clientes_bp.patch("/perfil/avatar")
@validar
@permission(customer)
def definir_avatar():
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    key = data.get("avatar")
    if not isinstance(key, str) or not key.strip():
        return err_json("VALIDATION_FAILED", "Informe a imagem (chave do upload).", status=400)
    key = key.strip()
    # API-002: a chave precisa existir neste armazenamento.
    if not storage.key_exists(key):
        return err_json("VALIDATION_FAILED", "Imagem inválida ou inexistente.", status=400)
    id_usuario = g.current_user.cliente.id_usuario
    try:
        cliente = CRUD.update.cliente(id_usuario, {"avatar": key})
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao definir avatar do cliente %s.", id_usuario)
        return err_json("DATABASE_ERROR", "Não foi possível salvar a imagem.", status=500)
    return jsonify({"success": True, "avatar": storage.url_for_key(cliente.avatar) if cliente.avatar else None})


@clientes_bp.get("/favoritos")
@validar
@permission(customer)
def listar_favoritos():
    """IDs dos restaurantes favoritados pelo cliente autenticado."""
    favoritos = CRUD.read.favoritos_cliente(
        filters={"id_usuario": g.current_user.cliente.id_usuario}
    )
    return jsonify({"favoritos": [f.id_restaurante for f in favoritos]})


@clientes_bp.post("/favoritos")
@validar
@permission(customer)
def adicionar_favorito():
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    id_restaurante = data.get("id_restaurante")
    if not isinstance(id_restaurante, int):
        return err_json("VALIDATION_FAILED", "Informe o id do restaurante.", status=400)
    if CRUD.read.restaurante(id_restaurante) is None:
        return err_json("NOT_FOUND", "Restaurante não encontrado.", status=404)
    id_usuario = g.current_user.cliente.id_usuario

    # Idempotente: favoritar de novo não duplica.
    if CRUD.read.favoritos_cliente(filters={"id_usuario": id_usuario, "id_restaurante": id_restaurante}, limit=1):
        return jsonify({"success": True, "id_restaurante": id_restaurante})
    try:
        CRUD.create.cliente_favorito(id_usuario=id_usuario, id_restaurante=id_restaurante)
    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": True, "id_restaurante": id_restaurante})
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao favoritar restaurante %s.", id_restaurante)
        return err_json("DATABASE_ERROR", "Não foi possível favoritar.", status=500)
    return jsonify({"success": True, "id_restaurante": id_restaurante}), 201


@clientes_bp.delete("/favoritos/<int:id_restaurante>")
@validar
@permission(customer)
def remover_favorito(id_restaurante):
    id_usuario = g.current_user.cliente.id_usuario
    try:
        CRUD.delete.cliente_favorito((id_usuario, id_restaurante))
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao remover favorito %s.", id_restaurante)
        return err_json("DATABASE_ERROR", "Não foi possível remover o favorito.", status=500)
    return jsonify({"success": True})


from decimal import Decimal, InvalidOperation

# Recarga de saldo por SIMULAÇÃO (não há gateway real). Valores limitados para evitar abuso.
# shortcut: recarga fake; trocar por pagamento/entrada real quando houver gateway.
RECARGA_MIN = 1
RECARGA_MAX = 1000


@clientes_bp.get("/perfil/saldo")
@validar
@permission(customer)
def obter_saldo():
    return jsonify({"saldo": str(g.current_user.cliente.saldo)})


@clientes_bp.post("/perfil/saldo")
@validar
@permission(customer)
def adicionar_saldo():
    """Adiciona saldo simulado à conta do cliente (valor inteiro, entre R$1 e R$1000).

    O valor é tratado como INTEIRO (sem centavos): o frontend envia um número inteiro
    e aqui recusamos valores não-inteiros, negativos ou fora da faixa.
    """
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    valor_bruto = data.get("valor")
    # Aceita apenas inteiros (ou strings que representem inteiros). Rejeita decimais,
    # negativos e lixo. bool é subclasse de int, então barramos explicitamente.
    if isinstance(valor_bruto, bool):
        return err_json("VALIDATION_FAILED", "Informe um valor inteiro válido.", status=400)
    try:
        if isinstance(valor_bruto, float):
            raise ValueError("decimais não são permitidos")
        valor = int(str(valor_bruto).strip())
    except (TypeError, ValueError):
        return err_json("VALIDATION_FAILED", "Informe um valor inteiro válido (sem centavos).", status=400)
    if valor <= 0:
        return err_json("VALIDATION_FAILED", "O valor não pode ser negativo ou zero.", status=400)
    if valor < RECARGA_MIN or valor > RECARGA_MAX:
        return err_json("VALIDATION_FAILED", f"O valor deve estar entre R${RECARGA_MIN} e R${RECARGA_MAX}.", status=400)
    cliente = g.current_user.cliente
    try:
        # Mantém o saldo como inteiro (sem centavos), coerente com a recarga inteira.
        novo = int(Decimal(str(cliente.saldo))) + valor
        CRUD.update.cliente(cliente.id_usuario, {"saldo": novo})
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao adicionar saldo do cliente %s.", cliente.id_usuario)
        return err_json("DATABASE_ERROR", "Não foi possível adicionar saldo.", status=500)
    return jsonify({"success": True, "saldo": str(novo)})
