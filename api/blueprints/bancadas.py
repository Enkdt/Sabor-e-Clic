import logging
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from decorators import admin, permission, validar
from extensions import db
from models.crud import CRUD
from models.restaurante import Categoria, Restaurante
from validations import check_json
from utils import err_json


bancadas_bp = Blueprint("bancadas", __name__, url_prefix="/api/bancadas")
logger = logging.getLogger(__name__)

# Verificar se cozinheiros também terão essa permissão; provavelmente, sim.
@bancadas_bp.post("/restaurantes")
@validar
@permission(admin)
def criar_restaurante():
    """Cria um restaurante e associa suas categorias."""
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)

    nome = data.get("nome")
    nome = nome.strip() if isinstance(nome, str) else ""

    # Aceita tanto "categorias" quanto "categoria".
    category_input = data.get("categorias", data.get("categoria", []))
    if isinstance(category_input, str):
        category_input = [category_input]
    if not isinstance(category_input, list):
        category_input = []
    categories = list(dict.fromkeys(
        value.strip()
        for value in category_input
        if isinstance(value, str) and value.strip()
    ))

    # Validação dos campos.
    errors = {}
    if not nome:
        errors["nome"] = "Nome do restaurante é obrigatório."
    elif len(nome) > 30:
        errors["nome"] = "O nome deve ter no máximo 30 caracteres."
    if not categories:
        errors["categorias"] = "Informe ao menos uma categoria."
    elif any(len(category) > 30 for category in categories):
        errors["categorias"] = "Cada categoria deve ter no máximo 30 caracteres."
    if errors:
        return err_json("VALIDATION_FAILED", "Preencha os campos obrigatórios.", fields=errors, status=400)

    try:
        restaurante = CRUD.create.restaurante(nome=nome)
        for category_name in categories:
            existing = CRUD.read.categorias(filters={"nome": category_name}, limit=1)
            if existing:
                category = existing[0]
            else:
                category = CRUD.create.categoria(nome=category_name)
            CRUD.create.restaurante_categoria(
                id_restaurante=restaurante.id,
                id_categoria=category.id
            )

    except SQLAlchemyError:
        logger.exception("Falha ao criar restaurante e vincular categorias.")
        return err_json("DATABASE_ERROR", "Não foi possível criar o restaurante.", status=500)
    except ValueError as e:
        return err_json("VALIDATION_FAILED", str(e), status=400)
    logger.info("Restaurante %s criado com %s categoria(s).", restaurante.id, len(categories))
    return jsonify({
        "success": True,
        "restaurante": {
            "id": restaurante.id,
            "nome": restaurante.nome,
            "categorias": categories
        }
    }), 201