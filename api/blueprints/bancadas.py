import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from decorators import admin, cook, customer, permission, validar
from extensions import db
from models.crud import CRUD
from models import services
from models.restaurante import Categoria, Restaurante
from models.bancada import Bancada, Agendamento
from validations import check_json
from utils import err_json
import storage


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
        # Intervalos já ocupados (agendamentos aceitos) — o front mostra como indisponíveis.
        "ocupados": [
            {
                "inicio": ag.horario_agendado.isoformat(),
                "fim": (ag.horario_agendado + timedelta(minutes=ag.tempo_agendado)).isoformat(),
            }
            for ag in bancada.agendamento if ag.status == "aceito"
        ],
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


def _agendamento_json(ag):
    return {
        "id": ag.id,
        "id_bancada": ag.id_bancada,
        "bancada": (ag.bancada.bancada_endereco[0].complemento
                    if ag.bancada and ag.bancada.bancada_endereco and ag.bancada.bancada_endereco[0].complemento
                    else f"Bancada #{ag.id_bancada}"),
        "horario_agendado": ag.horario_agendado.isoformat(),
        "tempo_agendado": ag.tempo_agendado,
        "preco_total": str(ag.preco_total),
        "status": ag.status,
        "motivo_negacao": ag.motivo_negacao,
        "cliente": (ag.cliente.usuario.nome if ag.cliente else None),
    }


@bancadas_bp.post("/<int:bancada_id>/agendamentos")
@validar
@permission(customer)
def criar_agendamento(bancada_id):
    """O CLIENTE pede um agendamento (fica 'pendente'); cozinheiro/admin aceita ou nega depois.
    Cobra o preço do saldo do cliente ao pedir; negar estorna."""
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    bancada = db.session.get(Bancada, bancada_id)
    if bancada is None:
        return err_json("NOT_FOUND", "Bancada não encontrada.", status=404)

    try:
        inicio_raw = data.get("inicio")
        fim_raw = data.get("fim")
        if not isinstance(inicio_raw, str) or not isinstance(fim_raw, str):
            raise ValueError("Informe início e fim do agendamento.")
        # Exige data e hora (formato datetime-local: AAAA-MM-DDTHH:MM), não apenas data.
        if "T" not in inicio_raw or "T" not in fim_raw:
            raise ValueError("Informe data e hora (ex.: 2026-11-07T10:00).")
        horario = datetime.fromisoformat(inicio_raw)
        fim = datetime.fromisoformat(fim_raw)
        if horario.tzinfo is not None or fim.tzinfo is not None:
            raise ValueError("Informe os horários no fuso local da bancada.")
        segundos = (fim - horario).total_seconds()
        if segundos <= 0 or segundos % 60:
            raise ValueError("O horário final deve ser posterior ao início, em minutos inteiros.")
        duracao = int(segundos // 60)
        if duracao > 12 * 60:
            raise ValueError("O agendamento não pode exceder 12 horas.")
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
    except (TypeError, ValueError, InvalidOperation) as error:
        return err_json("VALIDATION_FAILED", str(error) or "Preencha os dados do agendamento corretamente.", status=400)

    cliente = g.current_user.cliente

    try:
        # Débito atômico + criação do agendamento 'pendente' em uma transação.
        agendamento = services.criar_agendamento_com_debito(
            id_cliente=cliente.id_usuario,
            id_bancada=bancada_id,
            horario=horario,
            duracao=duracao,
            preco=preco,
        )
    except services.DomainError as error:
        return err_json(error.code, error.message, status=error.status)
    except ValueError as error:
        db.session.rollback()
        return err_json("BOOKING_CONFLICT", str(error), status=409)
    except IntegrityError:
        db.session.rollback()
        return err_json("BOOKING_CONFLICT", "A bancada já tem um agendamento nesse intervalo.", status=409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao criar agendamento para a bancada %s.", bancada_id)
        return err_json("DATABASE_ERROR", "Não foi possível criar o agendamento.", status=500)

    return jsonify({"success": True, "agendamento": _agendamento_json(agendamento)}), 201


@bancadas_bp.get("/meus-agendamentos")
@validar
@permission(customer)
def meus_agendamentos():
    """Agendamentos do cliente autenticado (todos os status)."""
    ags = CRUD.read.agendamentos(filters={"id_cliente": g.current_user.cliente.id_usuario})
    ags = sorted(ags, key=lambda a: a.id, reverse=True)
    return jsonify({"agendamentos": [_agendamento_json(a) for a in ags]})


def _restaurantes_do_cozinheiro():
    """IDs de restaurantes aos quais o cozinheiro autenticado está filiado."""
    cozinheiro = getattr(g.current_user, "cozinheiro", None)
    if cozinheiro is None:
        return set()
    return {r.id for r in cozinheiro.restaurantes}


def _pode_gerenciar_agendamento(ag):
    """SEC-002: admin gerencia tudo; cozinheiro só agendamentos de bancadas de um
    restaurante ao qual está filiado. Bancada sem dono (id_restaurante None) é
    exclusiva do admin."""
    if g.current_role == "admin":
        return True
    if g.current_role != "cook":
        return False
    bancada = ag.bancada
    if bancada is None or bancada.id_restaurante is None:
        return False
    return bancada.id_restaurante in _restaurantes_do_cozinheiro()


@bancadas_bp.get("/agendamentos/pendentes")
@validar
@permission((cook, admin))
def agendamentos_pendentes():
    """Fila de pedidos de bancada aguardando aceite, escopada por propriedade (SEC-002)."""
    ags = CRUD.read.agendamentos(filters={"status": "pendente"})
    # Filtra pelo que o usuário tem autoridade para gerenciar.
    ags = [a for a in ags if _pode_gerenciar_agendamento(a)]
    ags = sorted(ags, key=lambda a: a.id)
    return jsonify({"agendamentos": [_agendamento_json(a) for a in ags]})


@bancadas_bp.post("/agendamentos/<int:ag_id>/aceitar")
@validar
@permission((cook, admin))
def aceitar_agendamento(ag_id):
    ag = CRUD.read.agendamento(ag_id)
    if ag is None:
        return err_json("NOT_FOUND", "Agendamento não encontrado.", status=404)
    if not _pode_gerenciar_agendamento(ag):
        return err_json("PERMISSION_DENIED", "Você não gerencia agendamentos desta bancada.", status=403)
    try:
        # Transição condicional 'pendente'->'aceito' + revalidação de sobreposição, atômica.
        services.aceitar_agendamento(ag_id=ag_id)
    except services.DomainError as error:
        return err_json(error.code, error.message, status=error.status)
    except ValueError as error:
        db.session.rollback()
        return err_json("BOOKING_CONFLICT", str(error), status=409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao aceitar agendamento %s.", ag_id)
        return err_json("DATABASE_ERROR", "Não foi possível aceitar o agendamento.", status=500)
    return jsonify({"success": True, "agendamento": _agendamento_json(CRUD.read.agendamento(ag_id))})


@bancadas_bp.post("/agendamentos/<int:ag_id>/negar")
@validar
@permission((cook, admin))
def negar_agendamento(ag_id):
    data = request.get_json(silent=True)
    if not check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    motivo = data.get("motivo")
    motivo = motivo.strip() if isinstance(motivo, str) else ""
    if not motivo or len(motivo) > 200:
        return err_json("VALIDATION_FAILED", "Informe o motivo da recusa (até 200 caracteres).", status=400)
    ag = CRUD.read.agendamento(ag_id)
    if ag is None:
        return err_json("NOT_FOUND", "Agendamento não encontrado.", status=404)
    if not _pode_gerenciar_agendamento(ag):
        return err_json("PERMISSION_DENIED", "Você não gerencia agendamentos desta bancada.", status=403)
    try:
        # Transição condicional 'pendente'->'negado' + estorno atômico (sem estorno duplo).
        services.negar_agendamento(ag_id=ag_id, motivo=motivo)
    except services.DomainError as error:
        return err_json(error.code, error.message, status=error.status)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao negar agendamento %s.", ag_id)
        return err_json("DATABASE_ERROR", "Não foi possível negar o agendamento.", status=500)
    return jsonify({"success": True, "agendamento": _agendamento_json(CRUD.read.agendamento(ag_id))})


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
