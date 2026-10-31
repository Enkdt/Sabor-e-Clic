from argon2 import PasswordHasher
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from .usuario import (
    Cliente,
    ClienteEndereco,
    Cozinheiro,
    Funcionario,
    Turno,
    Usuario,
)

ph = PasswordHasher()

class CRUD:
    class create:
        @staticmethod
        def record(record):
            """Persist and return an initialized SQLAlchemy model instance."""
            if not isinstance(record, db.Model):
                raise TypeError("record must be an instance of a mapped model")
            db.session.add(record)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                raise
            return record

        # usuario.py
        @staticmethod
        def funcionario(nome:str, email:str, senha:str, nivel_permissao:int):
            try:
                user = Usuario(nome=nome, email=email, senha_hash=ph.hash(senha),email_verificado=False)
                func = Funcionario(nivel_permissao=nivel_permissao, usuario=user)
                db.session.add(func)
                db.session.commit()
                return func

            except SQLAlchemyError:
                db.session.rollback()
                raise

        @staticmethod
        def cozinheiro(nome:str, email:str, senha:str, especialidade:str):
            try:
                user = Usuario(nome=nome, email=email, senha_hash=ph.hash(senha),email_verificado=False)
                cozi = Cozinheiro(usuario=user, especialidade=especialidade)
                db.session.add(cozi)
                db.session.commit()
                return cozi
            except SQLAlchemyError:
                db.session.rollback()
                raise

        @staticmethod
        def turno(id_cozinheiro:int, inicio, fim, periodo):
            try:
                turn = Turno(id_cozinheiro=id_cozinheiro, inicio=inicio, fim=fim, periodo=periodo)
                db.session.add(turn)
                db.session.commit()
                return turn
            except SQLAlchemyError:
                db.session.rollback()
                raise

        @staticmethod
        def cliente_com_endereco(
            nome: str,
            email: str,
            senha: str,
            rua: str,
            numero: str,
            cep: str,
            pais: str,
            estado: str,
            cidade: str,
            bairro: str,
            complemento: str | None = None,
        ) -> Usuario:
            """Create a customer and address in one database transaction."""
            user = Usuario(
                nome=nome,
                email=email,
                senha_hash=ph.hash(senha),
                email_verificado=False,
            )
            cliente = Cliente(usuario=user)
            cliente.endereco.append(ClienteEndereco(
                rua=rua,
                numero=numero,
                complemento=complemento,
                cep=cep,
                pais=pais,
                estado=estado,
                cidade=cidade,
                bairro=bairro,
            ))
            db.session.add(cliente)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                raise
            return user

        # pedido.py

        # restaurante.py

        # bancada.py

        # associacao.py (não tenho certeza se precisamos)

    class read:
        @staticmethod
        def record(model, identity):
            """Return a row by primary key, or None when it does not exist.

            For composite primary keys, pass the key values as a tuple in the
            same order as the model's declared primary key.
            """
            _validate_model(model)
            return db.session.get(model, identity)

        @staticmethod
        def records(model, filters=None, *, limit=None, offset=0):
            """Read rows by equality filters with optional pagination."""
            _validate_model(model)
            if limit is not None and limit < 0:
                raise ValueError("limit cannot be negative")
            if offset < 0:
                raise ValueError("offset cannot be negative")

            statement = db.select(model)
            for field, value in (filters or {}).items():
                if not hasattr(model, field):
                    raise ValueError(f"Unknown {model.__name__} field: {field}")
                statement = statement.where(getattr(model, field) == value)
            if limit is not None:
                statement = statement.limit(limit)
            if offset:
                statement = statement.offset(offset)
            return db.session.execute(statement).scalars().all()

        @staticmethod
        def usuario_por_email(email: str) -> Usuario | None:
            try:
                statement = db.select(Usuario).where(Usuario.email == email)
                return db.session.execute(statement).scalar_one_or_none()
            except SQLAlchemyError:
                db.session.rollback()
                raise
    class update:
        @staticmethod
        def record(model, identity, changes, *, allowed_fields):
            """Apply an explicitly allowlisted field update and commit it.

            Returns the updated row, or None if the primary key is absent.
            This is a persistence operation only; callers must enforce
            authorization and validate domain-specific invariants first.
            """
            _validate_model(model)
            if not isinstance(changes, dict) or not changes:
                raise ValueError("changes must be a non-empty dictionary")

            allowed = set(allowed_fields)
            primary_keys = {column.key for column in inspect(model).primary_key}
            invalid = set(changes) - allowed
            invalid.update(set(changes) & primary_keys)
            if invalid:
                raise ValueError(f"Fields cannot be updated: {', '.join(sorted(invalid))}")
            for field in changes:
                if not hasattr(model, field):
                    raise ValueError(f"Unknown {model.__name__} field: {field}")

            record = db.session.get(model, identity)
            if record is None:
                return None
            for field, value in changes.items():
                setattr(record, field, value)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                raise
            return record

    class delete:
        @staticmethod
        def record(model, identity) -> bool:
            """Delete a row by primary key; return False when it is absent."""
            _validate_model(model)
            record = db.session.get(model, identity)
            if record is None:
                return False
            db.session.delete(record)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                raise
            return True


def _validate_model(model):
    """Keep generic CRUD operations restricted to mapped model classes."""
    if not isinstance(model, type) or not hasattr(model, "__table__"):
        raise TypeError("model must be a mapped SQLAlchemy model class")

