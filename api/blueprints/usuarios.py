import logging
from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import validations as val
from decorators import admin, permission, validar
from extensions import db
from models.crud import CRUD
from utils import err_json
import storage

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

STAFF_ROLES = {"cook", "admin"}


@usuarios_bp.post("/usuarios/staff")
@validar
@permission(admin)
def criar_staff():
    """Cria uma conta de staff (cook/admin). Somente admin. Conta já verificada."""
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)

    role = data.get("role")
    nome = data.get("nome")
    nome = nome.strip() if isinstance(nome, str) else ""
    email = data.get("email")
    email = email.strip() if isinstance(email, str) else ""
    password = data.get("password") if isinstance(data.get("password"), str) else ""

    errors = {}
    if role not in STAFF_ROLES:
        return err_json("VALIDATION_FAILED", f"Papel inválido. Use um de: {', '.join(sorted(STAFF_ROLES))}.", status=400)
    if not nome:
        errors["nome"] = "Nome é obrigatório."
    if not val.check_email(email):
        errors["email"] = "Email inválido."
    if not val.check_pwd_strength(password, [nome, email]):
        errors["password"] = "Senha fraca. Use pelo menos 8 caracteres e combine tipos variados."

    # Campos específicos por papel.
    especialidade = None
    nivel_permissao = None
    if role == "cook":
        especialidade = data.get("especialidade")
        especialidade = especialidade.strip() if isinstance(especialidade, str) else ""
        if not especialidade:
            errors["especialidade"] = "Informe a especialidade do cozinheiro."
    else:  # admin
        # nivel_permissao existe na coluna (1–5) mas não governa hierarquia; default 1.
        # shortcut: tiers de nivel_permissao não são aplicados; definir política se o produto exigir.
        raw = data.get("nivel_permissao", 1)
        if not isinstance(raw, int) or not (1 <= raw <= 5):
            errors["nivel_permissao"] = "Nível de permissão deve ser um inteiro entre 1 e 5."
        else:
            nivel_permissao = raw

    if errors:
        return err_json("VALIDATION_FAILED", "Corrija os campos destacados.", fields=errors, status=400)

    if CRUD.read.usuario_por_email(email) is not None:
        return err_json("USER_EXISTS", "Email já está registrado.", status=409)

    try:
        if role == "cook":
            profile = CRUD.create.cozinheiro(nome=nome, email=email, senha=password, especialidade=especialidade)
        else:
            profile = CRUD.create.funcionario(nome=nome, email=email, senha=password, nivel_permissao=nivel_permissao)
        CRUD.update.verificar_email(profile.id_usuario)
    except IntegrityError:
        db.session.rollback()
        return err_json("USER_EXISTS", "Email já está registrado.", status=409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao criar conta de staff.")
        return err_json("DATABASE_ERROR", "Não foi possível criar a conta.", status=500)

    logger.info("Conta de staff criada: papel=%s.", role)
    return jsonify({
        "success": True,
        "usuario": {"id": profile.id_usuario, "nome": nome, "email": email, "role": role},
    }), 201


def _cozinheiro_json(coz):
    return {
        "id_usuario": coz.id_usuario,
        "nome": coz.usuario.nome,
        "email": coz.usuario.email,
        "especialidade": coz.especialidade,
        "restaurantes": [{"id": r.id, "nome": r.nome, "slug": r.slug} for r in coz.restaurantes],
    }


@usuarios_bp.get("/usuarios/cozinheiros")
@validar
@permission(admin)
def listar_cozinheiros():
    """Lista cozinheiros com os restaurantes a que estão filiados (para a tela de staff do admin)."""
    cozinheiros = CRUD.read.cozinheiros()
    return jsonify({"cozinheiros": [_cozinheiro_json(c) for c in cozinheiros]})


@usuarios_bp.post("/usuarios/cozinheiros/<int:id_usuario>/restaurantes")
@validar
@permission(admin)
def filiar_cozinheiro(id_usuario):
    """Admin filia um cozinheiro a um restaurante (N-N)."""
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    id_restaurante = data.get("id_restaurante")
    if not isinstance(id_restaurante, int):
        return err_json("VALIDATION_FAILED", "Informe o id do restaurante.", status=400)
    if CRUD.read.cozinheiro(id_usuario) is None:
        return err_json("NOT_FOUND", "Cozinheiro não encontrado.", status=404)
    if CRUD.read.restaurante(id_restaurante) is None:
        return err_json("NOT_FOUND", "Restaurante não encontrado.", status=404)
    try:
        CRUD.create.cozinheiro_restaurante(id_usuario, id_restaurante)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao filiar cozinheiro %s ao restaurante %s.", id_usuario, id_restaurante)
        return err_json("DATABASE_ERROR", "Não foi possível filiar o cozinheiro.", status=500)
    return jsonify({"success": True, "cozinheiro": _cozinheiro_json(CRUD.read.cozinheiro(id_usuario))})


@usuarios_bp.delete("/usuarios/cozinheiros/<int:id_usuario>/restaurantes/<int:id_restaurante>")
@validar
@permission(admin)
def desfiliar_cozinheiro(id_usuario, id_restaurante):
    if CRUD.read.cozinheiro(id_usuario) is None:
        return err_json("NOT_FOUND", "Cozinheiro não encontrado.", status=404)
    try:
        CRUD.delete.cozinheiro_restaurante(id_usuario, id_restaurante)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao desfiliar cozinheiro %s do restaurante %s.", id_usuario, id_restaurante)
        return err_json("DATABASE_ERROR", "Não foi possível desfiliar o cozinheiro.", status=500)
    return jsonify({"success": True, "cozinheiro": _cozinheiro_json(CRUD.read.cozinheiro(id_usuario))})


@usuarios_bp.get("/perfil/foto")
@validar
def obter_foto():
    """Avatar do usuário autenticado (qualquer papel)."""
    perfil = g.current_user.cozinheiro or g.current_user.funcionario or g.current_user.cliente
    chave = getattr(perfil, "avatar", None) if perfil else None
    return jsonify({"avatar": storage.url_for_key(chave) if chave else None})


@usuarios_bp.patch("/perfil/foto")
@validar
def definir_foto():
    """Define o avatar do usuário autenticado no perfil correspondente ao seu papel."""
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    key = data.get("avatar")
    if not isinstance(key, str) or not key.strip():
        return err_json("VALIDATION_FAILED", "Informe a imagem (chave do upload).", status=400)
    key = key.strip()
    # API-002: a chave precisa existir neste armazenamento.
    if not storage.key_exists(key):
        return err_json("VALIDATION_FAILED", "Imagem inválida ou inexistente.", status=400)
    uid = g.current_user.id
    try:
        if g.current_role == "cook":
            CRUD.update.cozinheiro(uid, {"avatar": key})
        elif g.current_role == "admin":
            CRUD.update.funcionario(uid, {"avatar": key})
        else:
            CRUD.update.cliente(uid, {"avatar": key})
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao definir avatar do usuário %s.", uid)
        return err_json("DATABASE_ERROR", "Não foi possível salvar a imagem.", status=500)
    return jsonify({"success": True, "avatar": storage.url_for_key(key)})
