import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from decorators import admin, permission, validar
from extensions import db
from models.crud import CRUD
from models.restaurante import Categoria, Restaurante
from models.bancada import Bancada
from validations import check_json
from utils import err_json


bancadas_bp = Blueprint("bancadas", __name__, url_prefix="/api/bancadas")
logger = logging.getLogger(__name__)


def _bancada_json(bancada):
    endereco = bancada.bancada_endereco[0] if bancada.bancada_endereco else None
    return {
        "id": bancada.id,
        "nome": endereco.complemento if endereco and endereco.complemento else f"Bancada #{bancada.id}",
        "preco_hora": str(bancada.preco_hora),
        "endereco": ({
            "rua": endereco.rua,
            "numero": endereco.numero,
            "complemento": endereco.complemento,
            "bairro": endereco.bairro,
            "cidade": endereco.cidade,
            "estado": endereco.estado,
        } if endereco else None),
        "equipamentos": [{"nome": item.equipamento.nome, "tipo": item.equipamento.tipo, "quantidade": item.qtd}
                         for item in bancada.associacao_equipamento],
        "horarios_disponiveis": [{"inicio": faixa.inicio.strftime("%H:%M"), "fim": faixa.fim.strftime("%H:%M")}
                                 for faixa in bancada.bancada_horario_disponivel],
    }


@bancadas_bp.get("")
@validar
def listar_bancadas():
    bancadas = db.session.scalars(db.select(Bancada).order_by(Bancada.id)).all()
    return jsonify({"bancadas": [_bancada_json(item) for item in bancadas]})


@bancadas_bp.get("/<int:bancada_id>")
@validar
def obter_bancada(bancada_id):
    bancada = db.session.get(Bancada, bancada_id)
    if bancada is None:
        return err_json("NOT_FOUND", "Bancada não encontrada.", status=404)
    return jsonify({"bancada": _bancada_json(bancada)})


@bancadas_bp.post("/<int:bancada_id>/agendamentos")
@validar
def criar_agendamento(bancada_id):
    if g.current_user.cozinheiro is None:
        return err_json("PERMISSION_DENIED", "Somente cozinheiros podem agendar uma bancada.", status=403)
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    bancada = db.session.get(Bancada, bancada_id)
    if bancada is None:
        return err_json("NOT_FOUND", "Bancada não encontrada.", status=404)

    try:
        horario = datetime.fromisoformat(data.get("inicio", ""))
        fim = datetime.fromisoformat(data.get("fim", ""))
        if horario.tzinfo is not None or fim.tzinfo is not None:
            raise ValueError("Informe os horários no fuso local da bancada.")
        segundos = (fim - horario).total_seconds()
        if segundos <= 0 or segundos % 60:
            raise ValueError("O horário final deve ser posterior ao início, em minutos inteiros.")
        duracao = int(segundos // 60)
        if horario <= datetime.now():
            raise ValueError("A data e hora do agendamento devem estar no futuro.")
        if not any(
            horario.date() == fim.date()
            and horario.time() >= faixa.inicio
            and fim.time() <= faixa.fim
            for faixa in bancada.bancada_horario_disponivel
        ):
            raise ValueError("O período escolhido está fora dos horários disponíveis para esta bancada.")
        preco = (Decimal(str(bancada.preco_hora)) * Decimal(duracao) / Decimal(60)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        agendamento = CRUD.create.agendamento(
            id_cozinheiro=g.current_user.cozinheiro.id_usuario,
            id_bancada=bancada_id,
            horario_agendado=horario,
            tempo_agendado=duracao,
            preco_total=preco,
        )
    except (TypeError, ValueError, InvalidOperation) as error:
        return err_json("VALIDATION_FAILED", str(error) or "Preencha os dados do agendamento corretamente.", status=400)
    except IntegrityError:
        return err_json("BOOKING_CONFLICT", "A bancada já tem um agendamento nesse intervalo.", status=409)
    except SQLAlchemyError:
        logger.exception("Falha ao criar agendamento para a bancada %s.", bancada_id)
        return err_json("DATABASE_ERROR", "Não foi possível criar o agendamento.", status=500)

    return jsonify({"success": True, "agendamento": {
        "id": agendamento.id,
        "id_bancada": agendamento.id_bancada,
        "horario_agendado": agendamento.horario_agendado.isoformat(),
        "tempo_agendado": agendamento.tempo_agendado,
        "preco_total": str(agendamento.preco_total),
        "preco_hora": str(bancada.preco_hora),
    }}), 201

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
