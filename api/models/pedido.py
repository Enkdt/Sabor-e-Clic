from datetime import datetime, date, time
from sqlalchemy import CheckConstraint, ForeignKey, String, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db
from usuario import Cliente, Cozinheiro
from restaurante import Prato, Cardapio
from associacao import CozinheiroPedido, PedidoPrato, PedidoCardapio

class Pedido(db.Model):
    __tablename__ = 'pedido'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey('cliente.id_usuario'))
    data: Mapped[date] = mapped_column(nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    tempo_estimado: Mapped[int] = mapped_column(nullable=False)
    cliente: Mapped['Cliente'] = relationship(back_populates='pedido')
    cozinheiros: Mapped[list['Cozinheiro']] = relationship(secondary='cozinheiro_pedido', back_populates='pedidos')
    associacao_cozinheiro: Mapped[list['CozinheiroPedido']] = relationship(back_populates='pedido')
    pratos: Mapped[list['Prato']] = relationship(secondary='pedido_prato', back_populates='pedidos')
    associacao_prato: Mapped[list['PedidoPrato']] = relationship(back_populates='pedido')
    cardapios: Mapped[list['Cardapio']] = relationship(secondary='pedido_cardapio', back_populates='pedidos')
    associacao_cardapio: Mapped[list['PedidoCardapio']] = relationship(back_populates='pedido')
    __table_args__ = (
        CheckConstraint(
            "status IN ('preparando', 'pronto')", #TODO: Ajustar isso
            name='ck_pedido_status'
        ),
    )