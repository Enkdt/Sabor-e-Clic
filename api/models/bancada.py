from datetime import datetime, time
from sqlalchemy import CheckConstraint, ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db

class Agendamento(db.Model):
    __tablename__ = 'agendamento'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Fluxo novo: o CLIENTE pede; cozinheiro/admin aceita ou nega. id_cozinheiro fica para registro legado.
    id_cliente: Mapped[int | None] = mapped_column(ForeignKey('cliente.id_usuario'), nullable=True)
    id_cozinheiro: Mapped[int | None] = mapped_column(ForeignKey('cozinheiro.id_usuario'), nullable=True)
    id_bancada: Mapped[int] = mapped_column(ForeignKey('bancada.id'))
    horario_agendado: Mapped[datetime] = mapped_column(nullable=False)
    tempo_agendado: Mapped[int] = mapped_column(nullable=False)
    preco_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pendente')
    motivo_negacao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cliente: Mapped['Cliente'] = relationship()
    cozinheiro: Mapped['Cozinheiro'] = relationship(back_populates='agendamento')
    bancada: Mapped['Bancada'] = relationship(back_populates='agendamento')
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendente','aceito','negado')",
            name='ck_agendamento_status'
        ),
    )

class Bancada(db.Model):
    __tablename__ = 'bancada'
    id: Mapped[int] = mapped_column(primary_key=True)
    preco_hora: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=40)
    agendamento: Mapped[list['Agendamento']] = relationship(back_populates='bancada')
    bancada_endereco: Mapped[list['BancadaEndereco']] = relationship(back_populates='bancada')
    bancada_horario_disponivel: Mapped[list['BancadaHorarioDisponivel']] = relationship(back_populates='bancada',cascade='all, delete-orphan')
    associacao_equipamento: Mapped[list['BancadaEquipamento']] = relationship(back_populates='bancada')

class BancadaEndereco(db.Model):
    __tablename__ = 'bancada_endereco'
    id_bancada: Mapped[int] = mapped_column(ForeignKey('bancada.id'), primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    rua: Mapped[str] = mapped_column(String(45), nullable=False)
    numero: Mapped[str] = mapped_column(String(5), nullable=False)
    complemento: Mapped[str] = mapped_column(String(45))
    bairro: Mapped[str] = mapped_column(String(45), nullable=False)
    cidade: Mapped[str] = mapped_column(String(45), nullable=False)
    estado: Mapped[str] = mapped_column(String(3), nullable=False)
    bancada: Mapped['Bancada'] = relationship(back_populates='bancada_endereco')

class BancadaHorarioDisponivel(db.Model):
    __tablename__ = 'bancada_horario_disponivel'
    id_bancada: Mapped[int] = mapped_column(ForeignKey('bancada.id'), primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    inicio: Mapped[time] = mapped_column(nullable=False)
    fim: Mapped[time] = mapped_column(nullable=False)
    bancada: Mapped['Bancada'] = relationship(back_populates='bancada_horario_disponivel')

class Equipamento(db.Model):
    __tablename__ = 'equipamento'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    associacao_bancada: Mapped[list['BancadaEquipamento']] = relationship(back_populates='equipamento')
