from datetime import date
from sqlalchemy import CheckConstraint, ForeignKey, String, Numeric
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
    cliente: Mapped['Cliente'] = relationship(back_populates='pedido')
    associacao_cozinheiro: Mapped[list['CozinheiroPedido']] = relationship(back_populates='pedido')
    associacao_prato: Mapped[list['PedidoPrato']] = relationship(back_populates='pedido')
    associacao_cardapio: Mapped[list['PedidoCardapio']] = relationship(back_populates='pedido')
    __table_args__ = (
        CheckConstraint(
            "status IN ('preparando', 'pronto')", # TODO: Ajustar isso.
            name='ck_pedido_status'
        ),
    )
