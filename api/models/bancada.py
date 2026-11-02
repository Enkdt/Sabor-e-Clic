from datetime import datetime, time
from sqlalchemy import ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db

class Agendamento(db.Model): # TODO: Impedir agendamentos sobrepostos.
    __tablename__ = 'agendamento'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cozinheiro: Mapped[int] = mapped_column(ForeignKey('cozinheiro.id_usuario'))
    id_bancada: Mapped[int] = mapped_column(ForeignKey('bancada.id'))
    horario_agendado: Mapped[datetime] = mapped_column(nullable=False)
    tempo_agendado: Mapped[int] = mapped_column(nullable=False)
    preco_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    cozinheiro: Mapped['Cozinheiro'] = relationship(back_populates='agendamento')
    bancada: Mapped['Bancada'] = relationship(back_populates='agendamento')

class Bancada(db.Model):
    __tablename__ = 'bancada'
    id: Mapped[int] = mapped_column(primary_key=True)
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