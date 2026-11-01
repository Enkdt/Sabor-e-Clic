from datetime import datetime, time
from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(90), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verificado: Mapped[bool] = mapped_column(nullable=False, default=False)
    auth_version: Mapped[int] = mapped_column(nullable=False, default=1)
    funcionario: Mapped['Funcionario | None'] = relationship(back_populates='usuario')
    cozinheiro: Mapped['Cozinheiro | None'] = relationship(back_populates='usuario')
    cliente: Mapped['Cliente | None'] = relationship(back_populates='usuario')

    @property
    def role(self) -> str | None:
        """Papel é derivado do tipo do user, caso hajam multiplos, herda permissões do de maior privilégio"""
        roles = [
            role for role, profile in (
            ('admin', self.funcionario),
            ('cook', self.cozinheiro),
            ('customer', self.cliente),
            )
            if profile is not None
        ]
        # Impede que uma conta com vários perfis herde o maior nível de privilégio.
        return roles[0] if len(roles) == 1 else None

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('usuario.id'), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    usuario: Mapped['Usuario'] = relationship()

class Funcionario(db.Model):
    __tablename__ = 'funcionario'
    id_usuario: Mapped[int] = mapped_column(ForeignKey('usuario.id'), primary_key=True)
    nivel_permissao: Mapped[int] = mapped_column(nullable=False)
    usuario: Mapped['Usuario'] = relationship(back_populates='funcionario')
    __table_args__ = (
        CheckConstraint(
            "nivel_permissao BETWEEN 1 AND 5", # TODO: Ajustar isso.
            name='ck_funcionario_nivel_permissao'
            ),
        ) 

class Cozinheiro(db.Model):
    __tablename__ = 'cozinheiro'
    id_usuario: Mapped[int] = mapped_column(ForeignKey('usuario.id'), primary_key=True)
    especialidade: Mapped[str] = mapped_column(String(60), nullable=False)
    usuario: Mapped['Usuario'] = relationship(back_populates='cozinheiro')
    turno: Mapped[list['Turno']] = relationship(back_populates='cozinheiro', cascade='all, delete-orphan')
    agendamento: Mapped[list['Agendamento']] = relationship(back_populates='cozinheiro')
    associacao_pedido: Mapped[list['CozinheiroPedido']] = relationship(back_populates='cozinheiro')


class Turno(db.Model):
    __tablename__ = 'turno'
    id_turno: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cozinheiro: Mapped[int] = mapped_column(ForeignKey('cozinheiro.id_usuario'), nullable=False)
    inicio: Mapped[time] = mapped_column(nullable=False)
    fim: Mapped[time] = mapped_column(nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    cozinheiro: Mapped['Cozinheiro'] = relationship(back_populates='turno')
    __table_args__ = (
        CheckConstraint(
            "periodo IN ('matutino','vespertino','noturno')",
            name='ck_turno_periodo'
        ),
    )

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id_usuario: Mapped[int] = mapped_column(ForeignKey('usuario.id'), primary_key=True)
    endereco: Mapped[list['ClienteEndereco']] = relationship(back_populates='cliente', cascade='all, delete-orphan')
    usuario: Mapped['Usuario'] = relationship(back_populates='cliente')
    pedido: Mapped[list['Pedido']] = relationship(back_populates='cliente')

class ClienteEndereco(db.Model):
    __tablename__ = 'cliente_endereco'
    id_usuario: Mapped[int] = mapped_column(ForeignKey('cliente.id_usuario'),nullable=False)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True) # Número que diferencia este endereço dos demais.
    rua: Mapped[str] = mapped_column(String(45), nullable=False)
    numero: Mapped[str] = mapped_column(String(5), nullable=False)
    complemento: Mapped[str| None] = mapped_column(String(45),nullable=True)
    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    pais: Mapped[str] = mapped_column(String(45), nullable=False)
    bairro: Mapped[str] = mapped_column(String(45), nullable=False)
    cidade: Mapped[str] = mapped_column(String(45), nullable=False)
    estado: Mapped[str] = mapped_column(String(3), nullable=False) # Sigla do estado, como SP, RJ ou MG.
    cliente: Mapped['Cliente'] = relationship(back_populates='endereco')
