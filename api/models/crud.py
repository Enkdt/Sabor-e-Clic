from datetime import date, datetime, time
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import logging
import math

from argon2 import PasswordHasher
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String, Time, inspect
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from .usuario import (
    Cliente, ClienteEndereco, ClienteFavorito, Cozinheiro, Funcionario, PasswordResetToken,
    Turno, Usuario,
)
from .pedido import Pedido, Avaliacao
from .restaurante import (
    Cardapio, Categoria, Ingrediente, Prato, Restaurante, RestauranteEndereco,
    restaurante_categoria,
)
from .bancada import (
    Agendamento, Bancada, BancadaEndereco, BancadaHorarioDisponivel, Equipamento,
)
from .associacao import (
    BancadaEquipamento, CozinheiroPedido, PedidoCardapio, PedidoPrato,
    PratoCategoria, PratoIngrediente,
)

ph = PasswordHasher()
logger = logging.getLogger(__name__)

# Exemplo de como chamar o crud, caso esteja confuso
# CRUD.create.pedido(
#     id_cliente=cliente_id,
#     data=data,
#     total=25.50,
#     status="preparando",
#     tempo_estimado=30,
# )

class CRUD:
    class create:
        @staticmethod
        def usuario(nome: str, email: str, senha: str) -> Usuario:
            _validate_credentials(nome, email, senha)
            return _create(Usuario, {
                "nome": nome.strip(),
                "email": email.strip().lower(),
                "senha_hash": ph.hash(senha),
                "email_verificado": False,
            })

        @staticmethod
        def funcionario(nome: str, email: str, senha: str, nivel_permissao: int):
            return _create_user_profile(
                Funcionario,
                nome,
                email,
                senha,
                {"nivel_permissao": nivel_permissao},
            )

        @staticmethod
        def cozinheiro(nome: str, email: str, senha: str, especialidade: str):
            return _create_user_profile(
                Cozinheiro,
                nome,
                email,
                senha,
                {"especialidade": especialidade.strip() if isinstance(especialidade, str) else especialidade},
            )

        @staticmethod
        def cliente_com_endereco(
            nome: str, email: str, senha: str, rua: str, numero: str, cep: str,
            pais: str, estado: str, cidade: str, bairro: str,
            complemento: str | None = None,
        ) -> Usuario:
            _validate_credentials(nome, email, senha)
            address = {
                "rua": rua, "numero": numero, "cep": cep, "pais": pais,
                "estado": estado, "cidade": cidade, "bairro": bairro,
                "complemento": complemento,
            }
            _validate_data(ClienteEndereco, address, partial=True)
            user = Usuario(
                nome=nome.strip(), email=email.strip().lower(),
                senha_hash=ph.hash(senha), email_verificado=False,
            )
            _create(
                Cliente,
                {},
                relationships={
                    "usuario": user,
                    "endereco": [ClienteEndereco(**address)],
                },
                partial=True,
            )
            return user

        @staticmethod
        def turno(id_cozinheiro: int, inicio: time, fim: time, periodo: str):
            return _create(Turno, {
                "id_cozinheiro": id_cozinheiro, "inicio": inicio,
                "fim": fim, "periodo": periodo,
            })

        @staticmethod
        def password_reset_token(**dados):
            return _create(PasswordResetToken, dados)

        @staticmethod
        def cliente(**dados):
            return _create(Cliente, dados)

        @staticmethod
        def cliente_endereco(**dados):
            return _create(ClienteEndereco, dados)

        @staticmethod
        def cliente_favorito(**dados):
            return _create(ClienteFavorito, dados)

        @staticmethod
        def pedido(**dados):
            return _create(Pedido, dados)

        @staticmethod
        def avaliacao(**dados):
            return _create(Avaliacao, dados)

        @staticmethod
        def cardapio(**dados):
            return _create(Cardapio, dados)

        @staticmethod
        def restaurante(**dados):
            return _create(Restaurante, dados)

        @staticmethod
        def restaurante_endereco(**dados):
            return _create(RestauranteEndereco, dados)

        @staticmethod
        def prato(**dados):
            return _create(Prato, dados)

        @staticmethod
        def categoria(**dados):
            return _create(Categoria, dados)

        @staticmethod
        def ingrediente(**dados):
            return _create(Ingrediente, dados)

        @staticmethod
        def agendamento(**dados):
            return _create(Agendamento, dados)

        @staticmethod
        def bancada(**dados):
            return _create(Bancada, dados)

        @staticmethod
        def bancada_endereco(**dados):
            return _create(BancadaEndereco, dados)

        @staticmethod
        def bancada_horario_disponivel(**dados):
            return _create(BancadaHorarioDisponivel, dados)

        @staticmethod
        def equipamento(**dados):
            return _create(Equipamento, dados)

        @staticmethod
        def cozinheiro_pedido(**dados):
            return _create(CozinheiroPedido, dados)

        @staticmethod
        def bancada_equipamento(**dados):
            return _create(BancadaEquipamento, dados)

        @staticmethod
        def pedido_prato(**dados):
            return _create(PedidoPrato, dados)

        @staticmethod
        def pedido_cardapio(**dados):
            return _create(PedidoCardapio, dados)

        @staticmethod
        def prato_ingrediente(**dados):
            return _create(PratoIngrediente, dados)

        @staticmethod
        def prato_categoria(**dados):
            return _create(PratoCategoria, dados)

        @staticmethod
        def restaurante_categoria(id_restaurante: int, id_categoria: int):
            return _create_restaurante_categoria(id_restaurante, id_categoria)

        @staticmethod
        def cozinheiro_restaurante(id_cozinheiro: int, id_restaurante: int):
            return _add_cozinheiro_restaurante(id_cozinheiro, id_restaurante)


    class read:
        @staticmethod
        def usuario(identity):
            return _read_one(Usuario, identity)

        @staticmethod
        def usuarios(filters=None, *, limit=None, offset=0):
            return _read_many(Usuario, filters, limit=limit, offset=offset)

        @staticmethod
        def password_reset_token(identity):
            return _read_one(PasswordResetToken, identity)

        @staticmethod
        def tokens_redefinicao_senha(filters=None, *, limit=None, offset=0):
            return _read_many(PasswordResetToken, filters, limit=limit, offset=offset)

        @staticmethod
        def funcionario(identity):
            return _read_one(Funcionario, identity)

        @staticmethod
        def funcionarios(filters=None, *, limit=None, offset=0):
            return _read_many(Funcionario, filters, limit=limit, offset=offset)

        @staticmethod
        def cozinheiro(identity):
            return _read_one(Cozinheiro, identity)

        @staticmethod
        def cozinheiros(filters=None, *, limit=None, offset=0):
            return _read_many(Cozinheiro, filters, limit=limit, offset=offset)

        @staticmethod
        def turno(identity):
            return _read_one(Turno, identity)

        @staticmethod
        def turnos(filters=None, *, limit=None, offset=0):
            return _read_many(Turno, filters, limit=limit, offset=offset)

        @staticmethod
        def cliente(identity):
            return _read_one(Cliente, identity)

        @staticmethod
        def clientes(filters=None, *, limit=None, offset=0):
            return _read_many(Cliente, filters, limit=limit, offset=offset)

        @staticmethod
        def cliente_endereco(identity):
            return _read_one(ClienteEndereco, identity)

        @staticmethod
        def enderecos_cliente(filters=None, *, limit=None, offset=0):
            return _read_many(ClienteEndereco, filters, limit=limit, offset=offset)

        @staticmethod
        def favoritos_cliente(filters=None, *, limit=None, offset=0):
            return _read_many(ClienteFavorito, filters, limit=limit, offset=offset)

        @staticmethod
        def pedido(identity):
            return _read_one(Pedido, identity)

        @staticmethod
        def pedidos(filters=None, *, limit=None, offset=0):
            return _read_many(Pedido, filters, limit=limit, offset=offset)

        @staticmethod
        def avaliacao(identity):
            return _read_one(Avaliacao, identity)

        @staticmethod
        def avaliacoes(filters=None, *, limit=None, offset=0):
            return _read_many(Avaliacao, filters, limit=limit, offset=offset)

        @staticmethod
        def cardapio(identity):
            return _read_one(Cardapio, identity)

        @staticmethod
        def cardapios(filters=None, *, limit=None, offset=0):
            return _read_many(Cardapio, filters, limit=limit, offset=offset)

        @staticmethod
        def restaurante(identity):
            return _read_one(Restaurante, identity)

        @staticmethod
        def restaurantes(filters=None, *, limit=None, offset=0):
            return _read_many(Restaurante, filters, limit=limit, offset=offset)

        @staticmethod
        def restaurante_endereco(identity):
            return _read_one(RestauranteEndereco, identity)

        @staticmethod
        def enderecos_restaurante(filters=None, *, limit=None, offset=0):
            return _read_many(RestauranteEndereco, filters, limit=limit, offset=offset)

        @staticmethod
        def prato(identity):
            return _read_one(Prato, identity)

        @staticmethod
        def pratos(filters=None, *, limit=None, offset=0):
            return _read_many(Prato, filters, limit=limit, offset=offset)

        @staticmethod
        def categoria(identity):
            return _read_one(Categoria, identity)

        @staticmethod
        def categorias(filters=None, *, limit=None, offset=0):
            return _read_many(Categoria, filters, limit=limit, offset=offset)

        @staticmethod
        def ingrediente(identity):
            return _read_one(Ingrediente, identity)

        @staticmethod
        def ingredientes(filters=None, *, limit=None, offset=0):
            return _read_many(Ingrediente, filters, limit=limit, offset=offset)

        @staticmethod
        def agendamento(identity):
            return _read_one(Agendamento, identity)

        @staticmethod
        def agendamentos(filters=None, *, limit=None, offset=0):
            return _read_many(Agendamento, filters, limit=limit, offset=offset)

        @staticmethod
        def bancada(identity):
            return _read_one(Bancada, identity)

        @staticmethod
        def bancadas(filters=None, *, limit=None, offset=0):
            return _read_many(Bancada, filters, limit=limit, offset=offset)

        @staticmethod
        def bancada_endereco(identity):
            return _read_one(BancadaEndereco, identity)

        @staticmethod
        def enderecos_bancada(filters=None, *, limit=None, offset=0):
            return _read_many(BancadaEndereco, filters, limit=limit, offset=offset)

        @staticmethod
        def bancada_horario_disponivel(identity):
            return _read_one(BancadaHorarioDisponivel, identity)

        @staticmethod
        def horarios_disponiveis_bancada(filters=None, *, limit=None, offset=0):
            return _read_many(BancadaHorarioDisponivel, filters, limit=limit, offset=offset)

        @staticmethod
        def equipamento(identity):
            return _read_one(Equipamento, identity)

        @staticmethod
        def equipamentos(filters=None, *, limit=None, offset=0):
            return _read_many(Equipamento, filters, limit=limit, offset=offset)

        @staticmethod
        def cozinheiro_pedido(identity):
            return _read_one(CozinheiroPedido, identity)

        @staticmethod
        def cozinheiros_pedidos(filters=None, *, limit=None, offset=0):
            return _read_many(CozinheiroPedido, filters, limit=limit, offset=offset)

        @staticmethod
        def bancada_equipamento(identity):
            return _read_one(BancadaEquipamento, identity)

        @staticmethod
        def bancadas_equipamentos(filters=None, *, limit=None, offset=0):
            return _read_many(BancadaEquipamento, filters, limit=limit, offset=offset)

        @staticmethod
        def pedido_prato(identity):
            return _read_one(PedidoPrato, identity)

        @staticmethod
        def pedidos_pratos(filters=None, *, limit=None, offset=0):
            return _read_many(PedidoPrato, filters, limit=limit, offset=offset)

        @staticmethod
        def pedido_cardapio(identity):
            return _read_one(PedidoCardapio, identity)

        @staticmethod
        def pedidos_cardapios(filters=None, *, limit=None, offset=0):
            return _read_many(PedidoCardapio, filters, limit=limit, offset=offset)

        @staticmethod
        def prato_ingrediente(identity):
            return _read_one(PratoIngrediente, identity)

        @staticmethod
        def pratos_ingredientes(filters=None, *, limit=None, offset=0):
            return _read_many(PratoIngrediente, filters, limit=limit, offset=offset)

        @staticmethod
        def prato_categoria(identity):
            return _read_one(PratoCategoria, identity)

        @staticmethod
        def pratos_categorias(filters=None, *, limit=None, offset=0):
            return _read_many(PratoCategoria, filters, limit=limit, offset=offset)

        @staticmethod
        def restaurante_categoria(identity):
            return _read_restaurante_categoria(identity)

        @staticmethod
        def restaurantes_categorias(filters=None, *, limit=None, offset=0):
            return _read_restaurante_categories(filters, limit=limit, offset=offset)

        @staticmethod
        def usuario_por_email(email: str) -> Usuario | None:
            if not isinstance(email, str) or not email.strip():
                raise ValueError("O e-mail deve ser um texto não vazio.")
            try:
                statement = db.select(Usuario).where(Usuario.email == email.strip().lower())
                return db.session.execute(statement).scalar_one_or_none()
            except SQLAlchemyError:
                db.session.rollback()
                logger.exception("Falha ao buscar usuário pelo e-mail.")
                raise

    class update:
        @staticmethod
        def senha_usuario(id_usuario: int, nova_senha: str):
            _validate_identity(Usuario, id_usuario)
            if not isinstance(nova_senha, str) or len(nova_senha) < 8:
                raise ValueError("A senha deve ter ao menos 8 caracteres.")
            user = _read_one(Usuario, id_usuario)
            if user is None:
                return None
            user.senha_hash = ph.hash(nova_senha)
            user.auth_version += 1
            return _commit(user)

        @staticmethod
        def verificar_email(id_usuario: int):
            _validate_identity(Usuario, id_usuario)
            user = _read_one(Usuario, id_usuario)
            if user is None:
                return None
            user.email_verificado = True
            return _commit(user)

        @staticmethod
        def usuario(identity, changes):
            return _update_record(Usuario, identity, changes, _EDITABLE["usuario"])

        @staticmethod
        def password_reset_token(identity, changes):
            return _update_record(PasswordResetToken, identity, changes, _EDITABLE["password_reset_token"])

        @staticmethod
        def funcionario(identity, changes):
            return _update_record(Funcionario, identity, changes, _EDITABLE["funcionario"])

        @staticmethod
        def cozinheiro(identity, changes):
            return _update_record(Cozinheiro, identity, changes, _EDITABLE["cozinheiro"])

        @staticmethod
        def turno(identity, changes):
            return _update_record(Turno, identity, changes, _EDITABLE["turno"])

        @staticmethod
        def cliente(identity, changes):
            return _update_record(Cliente, identity, changes, _EDITABLE["cliente"])

        @staticmethod
        def cliente_endereco(identity, changes):
            return _update_record(ClienteEndereco, identity, changes, _EDITABLE["cliente_endereco"])

        @staticmethod
        def pedido(identity, changes):
            return _update_record(Pedido, identity, changes, _EDITABLE["pedido"])

        @staticmethod
        def cardapio(identity, changes):
            return _update_record(Cardapio, identity, changes, _EDITABLE["cardapio"])

        @staticmethod
        def restaurante(identity, changes):
            return _update_record(Restaurante, identity, changes, _EDITABLE["restaurante"])

        @staticmethod
        def restaurante_endereco(identity, changes):
            return _update_record(RestauranteEndereco, identity, changes, _EDITABLE["restaurante_endereco"])

        @staticmethod
        def prato(identity, changes):
            return _update_record(Prato, identity, changes, _EDITABLE["prato"])

        @staticmethod
        def categoria(identity, changes):
            return _update_record(Categoria, identity, changes, _EDITABLE["categoria"])

        @staticmethod
        def ingrediente(identity, changes):
            return _update_record(Ingrediente, identity, changes, _EDITABLE["ingrediente"])

        @staticmethod
        def agendamento(identity, changes):
            return _update_record(Agendamento, identity, changes, _EDITABLE["agendamento"])

        @staticmethod
        def bancada(identity, changes):
            return _update_record(Bancada, identity, changes, _EDITABLE["bancada"])

        @staticmethod
        def bancada_endereco(identity, changes):
            return _update_record(BancadaEndereco, identity, changes, _EDITABLE["bancada_endereco"])

        @staticmethod
        def bancada_horario_disponivel(identity, changes):
            return _update_record(BancadaHorarioDisponivel, identity, changes, _EDITABLE["bancada_horario_disponivel"])

        @staticmethod
        def equipamento(identity, changes):
            return _update_record(Equipamento, identity, changes, _EDITABLE["equipamento"])

        @staticmethod
        def cozinheiro_pedido(identity, changes):
            return _update_record(CozinheiroPedido, identity, changes, _EDITABLE["cozinheiro_pedido"])

        @staticmethod
        def bancada_equipamento(identity, changes):
            return _update_record(BancadaEquipamento, identity, changes, _EDITABLE["bancada_equipamento"])

        @staticmethod
        def pedido_prato(identity, changes):
            return _update_record(PedidoPrato, identity, changes, _EDITABLE["pedido_prato"])

        @staticmethod
        def pedido_cardapio(identity, changes):
            return _update_record(PedidoCardapio, identity, changes, _EDITABLE["pedido_cardapio"])

        @staticmethod
        def prato_ingrediente(identity, changes):
            return _update_record(PratoIngrediente, identity, changes, _EDITABLE["prato_ingrediente"])

        @staticmethod
        def prato_categoria(identity, changes):
            return _update_record(PratoCategoria, identity, changes, _EDITABLE["prato_categoria"])

        @staticmethod
        def restaurante_categoria(identity, changes):
            return _update_restaurante_categoria(identity, changes)


    class delete:

        @staticmethod
        def usuario(identity):
            return _delete_record(Usuario, identity)

        @staticmethod
        def password_reset_token(identity):
            return _delete_record(PasswordResetToken, identity)

        @staticmethod
        def funcionario(identity):
            return _delete_record(Funcionario, identity)

        @staticmethod
        def cozinheiro(identity):
            return _delete_record(Cozinheiro, identity)

        @staticmethod
        def cozinheiro_restaurante(id_cozinheiro: int, id_restaurante: int):
            return _remove_cozinheiro_restaurante(id_cozinheiro, id_restaurante)

        @staticmethod
        def turno(identity):
            return _delete_record(Turno, identity)

        @staticmethod
        def cliente(identity):
            return _delete_record(Cliente, identity)

        @staticmethod
        def cliente_endereco(identity):
            return _delete_record(ClienteEndereco, identity)

        @staticmethod
        def cliente_favorito(identity):
            return _delete_record(ClienteFavorito, identity)

        @staticmethod
        def pedido(identity):
            return _delete_record(Pedido, identity)

        @staticmethod
        def cardapio(identity):
            return _delete_record(Cardapio, identity)

        @staticmethod
        def restaurante(identity):
            return _delete_record(Restaurante, identity)

        @staticmethod
        def restaurante_endereco(identity):
            return _delete_record(RestauranteEndereco, identity)

        @staticmethod
        def prato(identity):
            return _delete_record(Prato, identity)

        @staticmethod
        def categoria(identity):
            return _delete_record(Categoria, identity)

        @staticmethod
        def ingrediente(identity):
            return _delete_record(Ingrediente, identity)

        @staticmethod
        def agendamento(identity):
            return _delete_record(Agendamento, identity)

        @staticmethod
        def bancada(identity):
            return _delete_record(Bancada, identity)

        @staticmethod
        def bancada_endereco(identity):
            return _delete_record(BancadaEndereco, identity)

        @staticmethod
        def bancada_horario_disponivel(identity):
            return _delete_record(BancadaHorarioDisponivel, identity)

        @staticmethod
        def equipamento(identity):
            return _delete_record(Equipamento, identity)

        @staticmethod
        def cozinheiro_pedido(identity):
            return _delete_record(CozinheiroPedido, identity)

        @staticmethod
        def bancada_equipamento(identity):
            return _delete_record(BancadaEquipamento, identity)

        @staticmethod
        def pedido_prato(identity):
            return _delete_record(PedidoPrato, identity)

        @staticmethod
        def pedido_cardapio(identity):
            return _delete_record(PedidoCardapio, identity)

        @staticmethod
        def prato_ingrediente(identity):
            return _delete_record(PratoIngrediente, identity)

        @staticmethod
        def prato_categoria(identity):
            return _delete_record(PratoCategoria, identity)

        @staticmethod
        def restaurante_categoria(identity):
            return _delete_restaurante_categoria(identity)



# Campos que podem ser alterados pelo CRUD de cada entidade. Identificadores,
# segredos, contadores calculados e vínculos de perfil não são editáveis aqui.
_EDITABLE = {
    "usuario": {"nome", "email"},
    "password_reset_token": {"expires_at", "used_at"},
    "funcionario": {"nivel_permissao", "avatar"},
    "cozinheiro": {"especialidade", "avatar"},
    "turno": {"inicio", "fim", "periodo"},
    "cliente": {"avatar", "saldo"},
    "cliente_endereco": {"rua", "numero", "complemento", "cep", "pais", "estado", "cidade", "bairro"},
    "pedido": {"data", "total", "status", "tempo_estimado", "metodo_pagamento"},
    "cardapio": {"nome", "tipo"},
    "restaurante": {"nome", "imagem", "slug"},
    "restaurante_endereco": {"rua", "numero", "complemento", "bairro", "cidade", "estado"},
    "prato": {"nome", "preco_unidade", "quantidade", "imagem", "descricao", "slug", "disponivel"},
    "categoria": {"nome"},
    "ingrediente": {"nome", "validade", "unidade", "quantidade", "imagem"},
    "agendamento": {"horario_agendado", "tempo_agendado", "preco_total", "status", "motivo_negacao"},
    "bancada": {"preco_hora", "id_restaurante"},
    "bancada_endereco": {"rua", "numero", "complemento", "bairro", "cidade", "estado"},
    "bancada_horario_disponivel": {"inicio", "fim"},
    "equipamento": {"nome", "tipo"},
    "cozinheiro_pedido": set(),
    "bancada_equipamento": {"qtd"},
    "pedido_prato": {"qtd", "preco_und", "preco_total", "status", "confirmado_em", "motivo_negacao"},
    "pedido_cardapio": set(),
    "prato_ingrediente": {"unidade_medida", "qtd"},
    "prato_categoria": set(),
}


def _create(model, data, *, relationships=None, partial=False, commit=True):
    # Valida, monta e persiste o modelo e seus relacionamentos em uma transação.
    _validate_data(model, data, partial=partial)
    if model is Agendamento:
        _ensure_booking_available(data)
    return _persist(model(**data, **(relationships or {})), commit=commit)


def _create_user_profile(profile_model, nome, email, senha, profile_data):
    # Cria usuário e perfil juntos, armazenando apenas o hash da senha.
    _validate_credentials(nome, email, senha)
    user = Usuario(
        nome=nome.strip(),
        email=email.strip().lower(),
        senha_hash=ph.hash(senha),
        email_verificado=False,
    )
    return _create(
        profile_model,
        profile_data,
        relationships={"usuario": user},
        partial=True,
    )


def _create_restaurante_categoria(id_restaurante, id_categoria):
    # Cria o vínculo muitos-para-muitos sem aceitar IDs de outras entidades.
    _validate_identity(Restaurante, id_restaurante)
    _validate_identity(Categoria, id_categoria)
    restaurant, category = _load_restaurant_category_entities(id_restaurante, id_categoria)
    if category in restaurant.categorias:
        return id_restaurante, id_categoria
    restaurant.categorias.append(category)
    _commit(restaurant)
    return id_restaurante, id_categoria


def _add_cozinheiro_restaurante(id_cozinheiro, id_restaurante):
    # Filia um cozinheiro a um restaurante (N-N). Idempotente. Só o admin chama.
    _validate_identity(Cozinheiro, id_cozinheiro)
    _validate_identity(Restaurante, id_restaurante)
    cozinheiro = _read_one(Cozinheiro, id_cozinheiro)
    restaurante = _read_one(Restaurante, id_restaurante)
    if restaurante not in cozinheiro.restaurantes:
        cozinheiro.restaurantes.append(restaurante)
        _commit(cozinheiro)
    return id_cozinheiro, id_restaurante


def _remove_cozinheiro_restaurante(id_cozinheiro, id_restaurante):
    _validate_identity(Cozinheiro, id_cozinheiro)
    _validate_identity(Restaurante, id_restaurante)
    cozinheiro = _read_one(Cozinheiro, id_cozinheiro)
    restaurante = _read_one(Restaurante, id_restaurante)
    if restaurante in cozinheiro.restaurantes:
        cozinheiro.restaurantes.remove(restaurante)
        _commit(cozinheiro)
    return id_cozinheiro, id_restaurante


def _read_restaurante_categoria(identity):
    # Consulta um vínculo de restaurante e categoria pela chave composta.
    id_restaurante, id_categoria = _validate_restaurante_categoria_identity(identity)
    try:
        statement = db.select(restaurante_categoria).where(
            restaurante_categoria.c.id_restaurante == id_restaurante,
            restaurante_categoria.c.id_categoria == id_categoria,
        )
        row = db.session.execute(statement).mappings().first()
        return dict(row) if row is not None else None
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao buscar vínculo entre restaurante e categoria.")
        raise


def _read_restaurante_categories(filters=None, *, limit=None, offset=0):
    # Lista vínculos com filtros por ID e paginação validados.
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("O limite deve ser um inteiro maior ou igual a zero.")
    if type(offset) is not int or offset < 0:
        raise ValueError("O deslocamento deve ser um inteiro maior ou igual a zero.")
    if filters is None:
        filters = {}
    if not isinstance(filters, dict):
        raise TypeError("Os filtros devem ser informados em um dicionário.")
    unknown = set(filters) - {"id_restaurante", "id_categoria"}
    if unknown:
        raise ValueError(f"Filtros desconhecidos: {', '.join(sorted(unknown))}.")
    for field, model in (("id_restaurante", Restaurante), ("id_categoria", Categoria)):
        if field in filters:
            _validate_identity(model, filters[field])

    statement = db.select(restaurante_categoria)
    for field, value in filters.items():
        statement = statement.where(getattr(restaurante_categoria.c, field) == value)
    if limit is not None:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)
    try:
        return [dict(row) for row in db.session.execute(statement).mappings().all()]
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao listar vínculos entre restaurantes e categorias.")
        raise


def _update_restaurante_categoria(identity, changes):
    # Atualiza um vínculo substituindo sua categoria de forma transacional.
    if not isinstance(changes, dict) or set(changes) != {"id_categoria"}:
        raise ValueError("Informe somente o novo id_categoria para atualizar o vínculo.")
    id_restaurante, id_categoria_antiga = _validate_restaurante_categoria_identity(identity)
    _validate_identity(Categoria, changes["id_categoria"])
    if _read_restaurante_categoria(identity) is None:
        return None
    restaurant, old_category = _load_restaurant_category_entities(
        id_restaurante, id_categoria_antiga
    )
    _, new_category = _load_restaurant_category_entities(
        id_restaurante, changes["id_categoria"]
    )
    if old_category.id == new_category.id:
        return id_restaurante, id_categoria_antiga
    restaurant.categorias.remove(old_category)
    if new_category not in restaurant.categorias:
        restaurant.categorias.append(new_category)
    _commit(restaurant)
    return id_restaurante, new_category.id


def _delete_restaurante_categoria(identity):
    # Remove somente o vínculo; restaurante e categoria permanecem intactos.
    id_restaurante, id_categoria = _validate_restaurante_categoria_identity(identity)
    if _read_restaurante_categoria(identity) is None:
        return False
    restaurant, category = _load_restaurant_category_entities(id_restaurante, id_categoria)
    restaurant.categorias.remove(category)
    _commit(restaurant)
    return True


def _validate_restaurante_categoria_identity(identity):
    # Valida os dois IDs que formam a chave da tabela associativa.
    if not isinstance(identity, tuple) or len(identity) != 2:
        raise ValueError("A chave do vínculo exige (id_restaurante, id_categoria).")
    id_restaurante, id_categoria = identity
    _validate_identity(Restaurante, id_restaurante)
    _validate_identity(Categoria, id_categoria)
    return id_restaurante, id_categoria


def _load_restaurant_category_entities(id_restaurante, id_categoria):
    # Carrega as entidades vinculadas antes de alterar a relação.
    try:
        restaurant = db.session.get(Restaurante, id_restaurante)
        category = db.session.get(Categoria, id_categoria)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao carregar restaurante e categoria do vínculo.")
        raise
    if restaurant is None:
        raise ValueError("O restaurante informado não existe.")
    if category is None:
        raise ValueError("A categoria informada não existe.")
    return restaurant, category


def _update_record(model, identity, changes, editable_fields, *, commit=True):
    # Limita alterações aos campos permitidos e valida o estado completo atualizado.
    if not isinstance(changes, dict) or not changes:
        raise ValueError("Informe ao menos um campo para atualizar.")
    changes = dict(changes)
    if model is Usuario:
        if isinstance(changes.get("email"), str):
            changes["email"] = changes["email"].strip().lower()
        if isinstance(changes.get("nome"), str):
            changes["nome"] = changes["nome"].strip()
    forbidden = set(changes) - editable_fields
    if forbidden:
        raise ValueError(
            f"Campos não permitidos para {model.__name__}: {', '.join(sorted(forbidden))}."
        )
    _validate_identity(model, identity)
    _validate_data(model, changes, partial=True)
    try:
        record = db.session.get(model, identity)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao carregar registro de %s para atualização.", model.__name__)
        raise
    if record is None:
        return None

    values = {column.key: getattr(record, column.key) for column in inspect(model).columns}
    values.update(changes)
    _validate_data(model, values, allow_primary=True)
    if model is Agendamento:
        _ensure_booking_available(values, exclude_id=record.id)
    for field, value in changes.items():
        setattr(record, field, value)
    return _commit(record, commit=commit)


def _delete_record(model, identity, *, commit=True):
    # Busca e exclui somente registros do modelo associado a esta operação.
    _validate_identity(model, identity)
    try:
        record = db.session.get(model, identity)
        if record is None:
            return False
        db.session.delete(record)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
    except SQLAlchemyError:
        if commit:
            db.session.rollback()
        logger.exception("Falha ao excluir registro de %s.", model.__name__)
        raise
    return True


def _read_one(model, identity):
    # Consulta uma chave primária simples ou composta do modelo solicitado.
    _validate_identity(model, identity)
    try:
        return db.session.get(model, identity)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao buscar registro de %s.", model.__name__)
        raise


def _read_many(model, filters=None, *, limit=None, offset=0):
    # Aplica filtros de igualdade e paginação sem permitir campos desconhecidos.
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("O limite deve ser um inteiro maior ou igual a zero.")
    if type(offset) is not int or offset < 0:
        raise ValueError("O deslocamento deve ser um inteiro maior ou igual a zero.")
    if filters is None:
        filters = {}
    if not isinstance(filters, dict):
        raise TypeError("Os filtros devem ser informados em um dicionário.")
    _validate_data(
        model, filters, partial=True, allow_primary=True, check_foreign_keys=False
    )
    statement = db.select(model)
    for field, value in filters.items():
        statement = statement.where(getattr(model, field) == value)
    if limit is not None:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)
    try:
        return db.session.execute(statement).scalars().all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao listar registros de %s.", model.__name__)
        raise


def _validate_data(model, data, *, partial=False, allow_primary=False, check_foreign_keys=True):
    # Confere colunas, obrigatoriedade, tipos, chaves e regras do domínio.
    if not isinstance(data, dict):
        raise TypeError("Os dados devem ser informados em um dicionário.")
    columns = {column.key: column for column in inspect(model).columns}
    unknown = set(data) - set(columns)
    if unknown:
        raise ValueError(f"Campos desconhecidos para {model.__name__}: {', '.join(sorted(unknown))}.")
    primary_keys = {column.key for column in inspect(model).primary_key}
    if not allow_primary:
        generated_primary_keys = {
            name for name in primary_keys
            if _is_generated_primary_key(columns[name], len(primary_keys))
        }
        supplied_generated_keys = generated_primary_keys.intersection(data)
        if supplied_generated_keys:
            raise ValueError(
                f"Não informe chaves geradas automaticamente: {', '.join(sorted(supplied_generated_keys))}."
            )

    if not partial:
        missing = [
            name for name, column in columns.items()
            if name not in data and not column.nullable and column.default is None
            and column.server_default is None
            and not (column.primary_key and _is_generated_primary_key(column, len(primary_keys)))
        ]
        if missing:
            raise ValueError(f"Campos obrigatórios ausentes para {model.__name__}: {', '.join(missing)}.")

    for name, value in data.items():
        column = columns[name]
        if value is None:
            if not column.nullable:
                raise ValueError(f"O campo {name} de {model.__name__} não pode ser nulo.")
            continue
        _validate_column_value(model, name, column.type, value)
    _validate_domain(model, data)
    if check_foreign_keys:
        _validate_foreign_keys(model, data)


def _validate_foreign_keys(model, data):
    # Confirma que cada chave estrangeira informada aponta para um registro existente.
    mapped_models = {
        mapper.local_table.name: mapper.class_
        for mapper in db.Model.registry.mappers
    }
    for column in inspect(model).columns:
        if column.key not in data or data[column.key] is None:
            continue
        for foreign_key in column.foreign_keys:
            target_table = foreign_key.column.table.name
            target_model = mapped_models.get(target_table)
            if target_model is None:
                continue
            try:
                target = db.session.get(target_model, data[column.key])
            except SQLAlchemyError:
                db.session.rollback()
                logger.exception("Falha ao validar referência de %s.%s.", model.__name__, column.key)
                raise
            if target is None:
                raise ValueError(
                    f"O campo {column.key} referencia um registro inexistente em {target_table}."
                )


def _is_generated_primary_key(column, primary_key_count):
    # Reconhece chaves inteiras que o banco preenche automaticamente.
    if column.autoincrement is True:
        return True
    return (
        column.autoincrement == "auto"
        and primary_key_count == 1
        and isinstance(column.type, Integer)
        and not column.foreign_keys
    )


def _validate_column_value(model, name, sql_type, value):
    # Confere o valor conforme o tipo SQL e os limites declarados pela coluna.
    valid = True
    if isinstance(sql_type, Boolean):
        valid = type(value) is bool
    elif isinstance(sql_type, Integer):
        valid = type(value) is int
    elif isinstance(sql_type, Float):
        try:
            valid = type(value) in {int, float} and math.isfinite(value)
        except OverflowError:
            valid = False
    elif isinstance(sql_type, Numeric):
        try:
            valid = type(value) in {int, float} or isinstance(value, Decimal)
            number = Decimal(str(value))
            valid = valid and not isinstance(value, bool) and number.is_finite()
            if valid and sql_type.precision is not None:
                integer_digits = max(number.adjusted() + 1, 0) if number else 0
                scale = max(0, -number.as_tuple().exponent)
                valid = integer_digits + scale <= sql_type.precision and scale <= (sql_type.scale or 0)
        except (InvalidOperation, ValueError):
            valid = False
    elif isinstance(sql_type, String):
        valid = isinstance(value, str) and len(value) <= (sql_type.length or len(value))
        if valid and not model.__table__.columns[name].nullable:
            valid = bool(value.strip())
    elif isinstance(sql_type, DateTime):
        valid = isinstance(value, datetime)
    elif isinstance(sql_type, Date):
        valid = isinstance(value, date) and not isinstance(value, datetime)
    elif isinstance(sql_type, Time):
        valid = isinstance(value, time)
    if not valid:
        raise ValueError(f"Valor inválido para o campo {name} de {model.__name__}.")


def _validate_domain(model, data):
    # Aplica restrições semânticas que não estão expressas pelos tipos SQL.
    if model is Usuario:
        if "email" in data and (not data["email"].strip() or "@" not in data["email"]):
            raise ValueError("Informe um endereço de e-mail válido.")
        if "nome" in data and not data["nome"].strip():
            raise ValueError("O nome não pode ficar vazio.")
        if "auth_version" in data and data["auth_version"] < 1:
            raise ValueError("A versão de autenticação deve ser positiva.")
    elif model is Funcionario and "nivel_permissao" in data and not 1 <= data["nivel_permissao"] <= 5:
        raise ValueError("O nível de permissão deve estar entre 1 e 5.")
    elif model is Turno:
        if "periodo" in data and data["periodo"] not in {"matutino", "vespertino", "noturno"}:
            raise ValueError("O período deve ser matutino, vespertino ou noturno.")
        if "inicio" in data and "fim" in data and data["inicio"] >= data["fim"]:
            raise ValueError("O início do turno deve ser anterior ao fim.")
    elif model is Pedido:
        if "status" in data and data["status"] not in {"preparando", "pronto", "pago"}:
            raise ValueError("O status do pedido deve ser preparando, pronto ou pago.")
        _nonnegative(data, "total", "tempo_estimado")
        if "tempo_estimado" in data and data["tempo_estimado"] == 0:
            raise ValueError("O tempo estimado do pedido deve ser maior que zero.")
    elif model in {Prato, Ingrediente}:
        _nonnegative(data, "quantidade")
        _nonnegative(data, "preco_unidade")
    elif model in {BancadaEquipamento, PedidoPrato, PratoIngrediente}:
        _nonnegative(data, "qtd", "preco_und", "preco_total")
    elif model is Agendamento:
        _nonnegative(data, "tempo_agendado", "preco_total")
        if "tempo_agendado" in data and data["tempo_agendado"] == 0:
            raise ValueError("A duração do agendamento deve ser maior que zero.")
    elif model is Bancada:
        _nonnegative(data, "preco_hora")
    elif model is PasswordResetToken:
        if "token_hash" in data and len(data["token_hash"]) != 64:
            raise ValueError("O hash do token deve conter 64 caracteres.")
    elif model is BancadaHorarioDisponivel:
        if "inicio" in data and "fim" in data and data["inicio"] >= data["fim"]:
            raise ValueError("O início da disponibilidade deve ser anterior ao fim.")


def _nonnegative(data, *fields):
    # Rejeita valores negativos nos campos quantitativos indicados.
    for field in fields:
        if field in data and data[field] < 0:
            raise ValueError(f"O campo {field} não pode ser negativo.")


def _ensure_booking_available(data, *, exclude_id=None):
    # Impede sobreposição com agendamentos ACEITOS da mesma bancada (pendentes não ocupam).
    # Só valida quando o próprio agendamento resultará em 'aceito' (ou não tem status: criação).
    if not {"id_bancada", "horario_agendado", "tempo_agendado"}.issubset(data):
        return
    if data.get("status") == "negado":
        return
    start = data["horario_agendado"]
    end = start + timedelta(minutes=data["tempo_agendado"])
    statement = db.select(Agendamento).where(
        Agendamento.id_bancada == data["id_bancada"],
        Agendamento.status == "aceito",
    )
    if exclude_id is not None:
        statement = statement.where(Agendamento.id != exclude_id)
    try:
        existing_bookings = db.session.execute(statement).scalars().all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao conferir disponibilidade da bancada %s.", data["id_bancada"])
        raise
    for existing in existing_bookings:
        existing_end = existing.horario_agendado + timedelta(minutes=existing.tempo_agendado)
        if start < existing_end and existing.horario_agendado < end:
            raise ValueError("A bancada já tem um agendamento nesse intervalo.")


def _validate_identity(model, identity):
    # Exige a quantidade e os tipos corretos de valores da chave primária.
    keys = list(inspect(model).primary_key)
    values = identity if isinstance(identity, tuple) else (identity,)
    if len(values) != len(keys):
        raise ValueError(f"A chave primária de {model.__name__} exige {len(keys)} valor(es).")
    for column, value in zip(keys, values):
        _validate_column_value(model, column.key, column.type, value)


def _validate_credentials(nome, email, senha):
    # Valida os dados de conta e a senha antes de gerar e armazenar o hash.
    _validate_data(Usuario, {
        "nome": nome.strip() if isinstance(nome, str) else nome,
        "email": email.strip().lower() if isinstance(email, str) else email,
        "senha_hash": "x" * 20,
        "email_verificado": False,
    })
    if not isinstance(senha, str) or len(senha) < 8:
        raise ValueError("A senha deve ter ao menos 8 caracteres.")


def _persist(record, *, commit=True):
    # Adiciona a instância à sessão e confirma (ou apenas faz flush em transação externa).
    db.session.add(record)
    return _commit(record, commit=commit)


def _commit(record, *, commit=True):
    # Confirma a transação ou, dentro de uma transação externa (commit=False),
    # apenas faz flush para disparar validações/erros do banco sem encerrar a transação.
    try:
        if commit:
            db.session.commit()
        else:
            db.session.flush()
    except SQLAlchemyError:
        if commit:
            db.session.rollback()
        logger.exception("Falha ao gravar %s.", type(record).__name__)
        raise
    return record

