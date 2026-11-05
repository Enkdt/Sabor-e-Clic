import logging
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from decorators import admin, cook, permission, validar
from extensions import db
from models.crud import CRUD
from validations import check_json
from utils import err_json, slugify
import storage


cardapio_bp = Blueprint("cardapio", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


def _prato_json(prato):
    return {
        "id": prato.id,
        "nome": prato.nome,
        "slug": prato.slug,
        "descricao": prato.descricao,
        "preco": str(prato.preco_unidade),
        "quantidade": prato.quantidade,
        "id_cardapio": prato.id_cardapio,
        "id_restaurante": prato.id_restaurante,
        "imagem": storage.url_for_key(prato.imagem) if prato.imagem else None,
        "categorias": [assoc.categoria.nome for assoc in prato.associacao_categoria],
        "ingredientes": [
            {
                "id_ingrediente": assoc.id_ingrediente,
                "nome": assoc.ingrediente.nome,
                "unidade_medida": assoc.unidade_medida,
                "qtd": str(assoc.qtd),
            }
            for assoc in prato.associacao_ingrediente
        ],
    }


def _restaurante_json(restaurante, *, incluir_pratos=False):
    dados = {
        "id": restaurante.id,
        "nome": restaurante.nome,
        "slug": restaurante.slug,
        "imagem": storage.url_for_key(restaurante.imagem) if restaurante.imagem else None,
        "categorias": [categoria.nome for categoria in restaurante.categorias],
    }
    if incluir_pratos:
        dados["pratos"] = [_prato_json(prato) for prato in restaurante.prato]
        dados["cardapios"] = [
            {"id": cardapio.id, "nome": cardapio.nome, "tipo": cardapio.tipo}
            for cardapio in {prato.cardapio for prato in restaurante.prato}
        ]
    return dados


def _buscar_restaurante(identificador):
    """Resolve um restaurante por slug (texto) ou id (numérico)."""
    if isinstance(identificador, str) and not identificador.isdigit():
        encontrados = CRUD.read.restaurantes(filters={"slug": identificador}, limit=1)
        return encontrados[0] if encontrados else None
    return CRUD.read.restaurante(int(identificador))


@cardapio_bp.get("/restaurantes")
def listar_restaurantes():
    restaurantes = CRUD.read.restaurantes()
    return jsonify({"restaurantes": [_restaurante_json(item) for item in restaurantes]})


@cardapio_bp.get("/restaurantes/<identificador>")
def obter_restaurante(identificador):
    restaurante = _buscar_restaurante(identificador)
    if restaurante is None:
        return err_json("NOT_FOUND", "Restaurante não encontrado.", status=404)
    return jsonify({"restaurante": _restaurante_json(restaurante, incluir_pratos=True)})


@cardapio_bp.get("/restaurantes/<rest>/pratos/<prato_slug>")
def obter_prato_do_restaurante(rest, prato_slug):
    """Único endpoint para obter um prato para exibição: pelo restaurante (slug ou id) + prato (slug ou id)."""
    restaurante = _buscar_restaurante(rest)
    if restaurante is None:
        return err_json("NOT_FOUND", "Restaurante não encontrado.", status=404)
    for p in restaurante.prato:
        if p.slug == prato_slug or str(p.id) == prato_slug:
            return jsonify({"prato": _prato_json(p)})
    return err_json("NOT_FOUND", "Prato não encontrado.", status=404)


@cardapio_bp.get("/pratos/<int:id>/avaliacoes")
def listar_avaliacoes_prato(id):
    """Avaliações públicas de um prato (lista + média). Leitura aberta (catálogo é público)."""
    prato = CRUD.read.prato(id)
    if prato is None:
        return err_json("NOT_FOUND", "Prato não encontrado.", status=404)
    avaliacoes = CRUD.read.avaliacoes(filters={"id_prato": id})
    avaliacoes = sorted(avaliacoes, key=lambda a: a.criado_em or 0, reverse=True)
    notas = [a.nota for a in avaliacoes]
    media = round(sum(notas) / len(notas), 1) if notas else None
    return jsonify({
        "media": media,
        "total": len(notas),
        "avaliacoes": [
            {
                "nota": a.nota,
                "comentario": a.comentario,
                "cliente": (a.cliente.usuario.nome if a.cliente and a.cliente.usuario else "Cliente"),
                "criado_em": a.criado_em.isoformat() if a.criado_em else None,
            }
            for a in avaliacoes
        ],
    })


# ---------------------------------------------------------------------------
# Criação de restaurante (somente admin)
# ---------------------------------------------------------------------------

def _slug_unico(nome):
    base = slugify(nome)
    slug = base
    n = 2
    while CRUD.read.restaurantes(filters={"slug": slug}, limit=1):
        slug = f"{base}-{n}"
        n += 1
    return slug


def _slug_prato_unico(id_restaurante, nome):
    """Slug de prato único DENTRO do restaurante (rota: /restaurante/<rslug>/prato/<pslug>)."""
    existentes = {p.slug for p in CRUD.read.pratos(filters={"id_restaurante": id_restaurante}) if p.slug}
    base = slugify(nome)
    slug = base
    n = 2
    while slug in existentes:
        slug = f"{base}-{n}"
        n += 1
    return slug


@cardapio_bp.post("/restaurantes")
@validar
@permission(admin)
def criar_restaurante():
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    nome = data.get("nome")
    nome = nome.strip() if isinstance(nome, str) else ""
    if not nome or len(nome) > 30:
        return err_json("VALIDATION_FAILED", "Informe um nome de restaurante (até 30 caracteres).", status=400)
    imagem = data.get("imagem")
    imagem = imagem.strip() if isinstance(imagem, str) and imagem.strip() else None
    try:
        restaurante = CRUD.create.restaurante(nome=nome, slug=_slug_unico(nome), imagem=imagem)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao criar restaurante.")
        return err_json("DATABASE_ERROR", "Não foi possível criar o restaurante.", status=500)
    return jsonify({"success": True, "restaurante": _restaurante_json(restaurante)}), 201


# ---------------------------------------------------------------------------
# Gestão de pratos (cozinheiro no próprio restaurante; admin em qualquer um)
# ---------------------------------------------------------------------------

def _pode_gerir_restaurante(id_restaurante):
    """Admin pode tudo; cozinheiro só nos restaurantes a que o admin o filiou."""
    if g.current_role == "admin":
        return True
    if g.current_role == "cook" and g.current_user.cozinheiro:
        return any(r.id == id_restaurante for r in g.current_user.cozinheiro.restaurantes)
    return False


def _parse_prato(data, *, partial=False):
    """Valida e normaliza os campos do prato. Retorna (valores, erros)."""
    errors = {}
    values = {}

    if not partial or "nome" in data:
        nome = data.get("nome")
        nome = nome.strip() if isinstance(nome, str) else ""
        if not nome or len(nome) > 50:
            errors["nome"] = "Informe o nome do prato (até 50 caracteres)."
        else:
            values["nome"] = nome

    if not partial or "preco" in data:
        try:
            preco = Decimal(str(data.get("preco")))
            if preco < 0:
                errors["preco"] = "O preço não pode ser negativo."
            else:
                values["preco_unidade"] = preco
        except (InvalidOperation, TypeError, ValueError):
            errors["preco"] = "Informe um preço numérico válido."

    if not partial or "quantidade" in data:
        q = data.get("quantidade")
        if not isinstance(q, int) or q < 0:
            errors["quantidade"] = "Informe uma quantidade inteira não negativa."
        else:
            values["quantidade"] = q

    if "descricao" in data:
        descricao = data.get("descricao")
        if descricao is None:
            values["descricao"] = None
        elif isinstance(descricao, str) and len(descricao) <= 300:
            values["descricao"] = descricao.strip() or None
        else:
            errors["descricao"] = "Descrição inválida (máx. 300 caracteres)."

    if "imagem" in data:
        imagem = data.get("imagem")
        if imagem is None:
            values["imagem"] = None
        elif isinstance(imagem, str) and imagem.strip():
            values["imagem"] = imagem.strip()
        else:
            errors["imagem"] = "Imagem inválida."

    return values, errors


def _parse_ingredientes(data):
    """Valida a lista opcional de ingredientes do prato. Retorna (lista, erro)."""
    itens = data.get("ingredientes")
    if itens is None:
        return None, None  # não mexe nos ingredientes
    if not isinstance(itens, list):
        return None, err_json("VALIDATION_FAILED", "ingredientes deve ser uma lista.", status=400)
    linhas = []
    for item in itens:
        if not isinstance(item, dict):
            return None, err_json("VALIDATION_FAILED", "Cada ingrediente deve ser um objeto.", status=400)
        id_ing = item.get("id_ingrediente")
        unidade = item.get("unidade_medida")
        qtd = item.get("qtd")
        if not isinstance(id_ing, int) or CRUD.read.ingrediente(id_ing) is None:
            return None, err_json("VALIDATION_FAILED", f"Ingrediente {id_ing} inexistente.", status=400)
        if not isinstance(unidade, str) or not unidade.strip() or len(unidade) > 20:
            return None, err_json("VALIDATION_FAILED", "unidade_medida inválida.", status=400)
        try:
            qtd_dec = Decimal(str(qtd))
            if qtd_dec <= 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError, ValueError):
            return None, err_json("VALIDATION_FAILED", "qtd de ingrediente inválida.", status=400)
        linhas.append((id_ing, unidade.strip(), qtd_dec))
    return linhas, None


def _aplicar_ingredientes(id_prato, linhas):
    """Substitui os ingredientes do prato pela lista informada."""
    existentes = CRUD.read.prato(id_prato).associacao_ingrediente
    for assoc in list(existentes):
        CRUD.delete.prato_ingrediente((id_prato, assoc.id_ingrediente))
    for id_ing, unidade, qtd in linhas:
        CRUD.create.prato_ingrediente(id_prato=id_prato, id_ingrediente=id_ing, unidade_medida=unidade, qtd=qtd)


@cardapio_bp.post("/restaurantes/<int:id_restaurante>/pratos")
@validar
@permission((cook, admin))
def criar_prato(id_restaurante):
    restaurante = CRUD.read.restaurante(id_restaurante)
    if restaurante is None:
        return err_json("NOT_FOUND", "Restaurante não encontrado.", status=404)
    if not _pode_gerir_restaurante(id_restaurante):
        return err_json("PERMISSION_DENIED", "Você não gerencia este restaurante.", status=403)

    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    values, errors = _parse_prato(data)
    if errors:
        return err_json("VALIDATION_FAILED", "Corrija os campos destacados.", fields=errors, status=400)
    linhas, erro = _parse_ingredientes(data)
    if erro:
        return erro

    # O prato precisa de um cardápio; reaproveita o primeiro do restaurante ou cria um padrão.
    cardapio_id = restaurante.prato[0].id_cardapio if restaurante.prato else CRUD.create.cardapio(nome="Cardápio", tipo="padrão").id
    try:
        prato = CRUD.create.prato(
            id_restaurante=id_restaurante,
            id_cardapio=cardapio_id,
            nome=values["nome"],
            slug=_slug_prato_unico(id_restaurante, values["nome"]),
            preco_unidade=values["preco_unidade"],
            quantidade=values["quantidade"],
            descricao=values.get("descricao"),
            imagem=values.get("imagem"),
        )
        if linhas:
            _aplicar_ingredientes(prato.id, linhas)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao criar prato no restaurante %s.", id_restaurante)
        return err_json("DATABASE_ERROR", "Não foi possível criar o prato.", status=500)
    return jsonify({"success": True, "prato": _prato_json(CRUD.read.prato(prato.id))}), 201


@cardapio_bp.patch("/pratos/<int:id>")
@validar
@permission((cook, admin))
def atualizar_prato(id):
    prato = CRUD.read.prato(id)
    if prato is None:
        return err_json("NOT_FOUND", "Prato não encontrado.", status=404)
    if not _pode_gerir_restaurante(prato.id_restaurante):
        return err_json("PERMISSION_DENIED", "Você não gerencia este prato.", status=403)

    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    values, errors = _parse_prato(data, partial=True)
    if errors:
        return err_json("VALIDATION_FAILED", "Corrija os campos destacados.", fields=errors, status=400)
    linhas, erro = _parse_ingredientes(data)
    if erro:
        return erro

    try:
        if values:
            CRUD.update.prato(id, values)
        if linhas is not None:
            _aplicar_ingredientes(id, linhas)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao atualizar prato %s.", id)
        return err_json("DATABASE_ERROR", "Não foi possível atualizar o prato.", status=500)
    return jsonify({"success": True, "prato": _prato_json(CRUD.read.prato(id))})


@cardapio_bp.delete("/pratos/<int:id>")
@validar
@permission((cook, admin))
def remover_prato(id):
    prato = CRUD.read.prato(id)
    if prato is None:
        return err_json("NOT_FOUND", "Prato não encontrado.", status=404)
    if not _pode_gerir_restaurante(prato.id_restaurante):
        return err_json("PERMISSION_DENIED", "Você não gerencia este prato.", status=403)
    try:
        for assoc in list(prato.associacao_ingrediente):
            CRUD.delete.prato_ingrediente((id, assoc.id_ingrediente))
        for assoc in list(prato.associacao_categoria):
            CRUD.delete.prato_categoria((id, assoc.id_categoria))
        CRUD.delete.prato(id)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao remover prato %s.", id)
        return err_json("DATABASE_ERROR", "Não foi possível remover o prato.", status=500)
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Imagens (restaurante: admin; prato: admin ou cozinheiro do restaurante)
# ---------------------------------------------------------------------------

def _imagem_do_corpo():
    """Lê e valida o campo 'imagem' (chave devolvida por POST /api/uploads). Retorna (key, erro)."""
    data = request.get_json(silent=True)
    if not check_json(data):
        return None, err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    key = data.get("imagem")
    if not isinstance(key, str) or not key.strip():
        return None, err_json("VALIDATION_FAILED", "Informe a imagem (chave do upload).", status=400)
    return key.strip(), None


@cardapio_bp.patch("/restaurantes/<int:id>/imagem")
@validar
@permission(admin)
def definir_imagem_restaurante(id):
    key, erro = _imagem_do_corpo()
    if erro:
        return erro
    try:
        restaurante = CRUD.update.restaurante(id, {"imagem": key})
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao definir imagem do restaurante %s.", id)
        return err_json("DATABASE_ERROR", "Não foi possível salvar a imagem.", status=500)
    if restaurante is None:
        return err_json("NOT_FOUND", "Restaurante não encontrado.", status=404)
    return jsonify({"success": True, "restaurante": _restaurante_json(restaurante)})


@cardapio_bp.patch("/pratos/<int:id>/imagem")
@validar
@permission((cook, admin))
def definir_imagem_prato(id):
    prato = CRUD.read.prato(id)
    if prato is None:
        return err_json("NOT_FOUND", "Prato não encontrado.", status=404)
    if not _pode_gerir_restaurante(prato.id_restaurante):
        return err_json("PERMISSION_DENIED", "Você não gerencia este prato.", status=403)
    key, erro = _imagem_do_corpo()
    if erro:
        return erro
    try:
        prato = CRUD.update.prato(id, {"imagem": key})
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao definir imagem do prato %s.", id)
        return err_json("DATABASE_ERROR", "Não foi possível salvar a imagem.", status=500)
    return jsonify({"success": True, "prato": _prato_json(prato)})
