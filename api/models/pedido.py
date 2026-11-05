from datetime import date, datetime, timezone
from sqlalchemy import CheckConstraint, ForeignKey, String, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db

class Pedido(db.Model):
    __tablename__ = 'pedido'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey('cliente.id_usuario'))
    data: Mapped[date] = mapped_column(nullable=False)
    total:  Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    tempo_estimado: Mapped[int] = mapped_column(nullable=False)
    metodo_pagamento: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cliente: Mapped['Cliente'] = relationship(back_populates='pedido')
    associacao_cozinheiro: Mapped[list['CozinheiroPedido']] = relationship(back_populates='pedido')
    associacao_prato: Mapped[list['PedidoPrato']] = relationship(back_populates='pedido')
    associacao_cardapio: Mapped[list['PedidoCardapio']] = relationship(back_populates='pedido')
    __table_args__ = (
        CheckConstraint(
            "status IN ('preparando', 'pronto', 'pago')",
            name='ck_pedido_status'
        ),
    )

class Avaliacao(db.Model):
    __tablename__ = 'avaliacao'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_pedido: Mapped[int] = mapped_column(ForeignKey('pedido.id'), nullable=False)
    # Avaliação por item do pedido: o restaurante é derivado via Prato.id_restaurante.
    id_prato: Mapped[int] = mapped_column(ForeignKey('prato.id'), nullable=False)
    id_cliente: Mapped[int] = mapped_column(ForeignKey('cliente.id_usuario'), nullable=False)
    nota: Mapped[int] = mapped_column(nullable=False)
    comentario: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(timezone.utc))
    pedido: Mapped['Pedido'] = relationship()
    prato: Mapped['Prato'] = relationship()
    cliente: Mapped['Cliente'] = relationship()
    __table_args__ = (
        CheckConstraint("nota BETWEEN 1 AND 5", name='ck_avaliacao_nota'),
        # Uma avaliação por prato dentro de um pedido.
        UniqueConstraint('id_pedido', 'id_prato', name='uq_avaliacao_pedido_prato'),
    )
