import logging
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from decorators import admin, permission, validar
from extensions import db
from models.restaurante import Categoria, Restaurante
from validations import check_json
from utils import err_json


bancadas_bp = Blueprint("bancadas", __name__, url_prefix="/api/bancadas")
logger = logging.getLogger(__name__)

#ver se permission vai ficar com cooks tbm, mas provável q sim
@bancadas_bp.post("/restaurantes")
@validar
@permission(admin)
def criar_restaurante():
    """Cria um restaurante a partir do json {nome:str, categorias:[list]}, tbd"""
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)

    nome = data.get("nome")
    nome = nome.strip() if isinstance(nome, str) else ""
    #esse aq é pq n teve a verifiação tá, ée pra deixar tudo no mesmo formato de list
    category_input = data.get("categorias", data.get("categoria", []))
    if isinstance(category_input, str):
        category_input = [category_input]
    if not isinstance(category_input, list):
        category_input = []
    categories = list(dict.fromkeys(
        value.strip() for value in category_input
        if isinstance(value, str) and value.strip()
    ))

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

    restaurante = Restaurante(nome=nome)
    for category_name in categories:
        category = db.session.execute(
            db.select(Categoria).where(Categoria.nome == category_name)
        ).scalar_one_or_none()
        if category is None:
            category = Categoria(nome=category_name)
        restaurante.categorias.append(category)

    db.session.add(restaurante)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Não foi possível criar o reestaurante")
        return err_json("DATABASE_ERROR", "Não foi possível criar o restaurante.", status=500)
    return jsonify({
        "success": True,
        "restaurante": {
            "id": restaurante.id,
            "nome": restaurante.nome,
            "categorias": [category.nome for category in restaurante.categorias],
        },
    }), 201
