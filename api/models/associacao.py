from datetime import datetime
from sqlalchemy import CheckConstraint, ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db

class CozinheiroPedido(db.Model):
    __tablename__ = 'cozinheiro_pedido'
    id_cozinheiro: Mapped[int] = mapped_column(ForeignKey('cozinheiro.id_usuario'), primary_key = True)
    id_pedido: Mapped[int] = mapped_column(ForeignKey('pedido.id'), primary_key = True)
    cozinheiro: Mapped['Cozinheiro'] = relationship(back_populates = 'associacao_pedido')
    pedido: Mapped['Pedido'] = relationship(back_populates = 'associacao_cozinheiro')

class BancadaEquipamento(db.Model):
    __tablename__ = 'bancada_equipamento'
    id_bancada: Mapped[int] = mapped_column(ForeignKey('bancada.id'), primary_key=True)
    id_equipamento: Mapped[int] = mapped_column(ForeignKey('equipamento.id'), primary_key=True)
    qtd: Mapped[int] = mapped_column(nullable = False)
    bancada: Mapped['Bancada'] = relationship(back_populates = 'associacao_equipamento')
    equipamento: Mapped['Equipamento'] = relationship(back_populates= 'associacao_bancada')

class PedidoPrato(db.Model):
    __tablename__ = 'pedido_prato'
    id_pedido: Mapped[int] = mapped_column(ForeignKey('pedido.id'), primary_key = True)
    id_prato: Mapped[int] = mapped_column(ForeignKey('prato.id'), primary_key = True)
    qtd: Mapped[int] = mapped_column(nullable = False)
    preco_und: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    preco_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    # Fluxo por item (cada restaurante confirma/nega o seu). A entrega é derivada do tempo (confirmado_em).
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='aguardando')
    confirmado_em: Mapped[datetime | None] = mapped_column(nullable=True)
    motivo_negacao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pedido: Mapped['Pedido'] = relationship(back_populates = 'associacao_prato')
    prato: Mapped['Prato'] = relationship(back_populates = 'associacao_pedido')
    __table_args__ = (
        CheckConstraint(
            "status IN ('aguardando','confirmado','preparando','pronto','entregue','negado')",
            name='ck_pedido_prato_status'
        ),
    )

class PedidoCardapio(db.Model):
    __tablename__ = 'pedido_cardapio'
    id_pedido: Mapped[int] = mapped_column(ForeignKey('pedido.id'), primary_key = True)
    id_cardapio: Mapped[int] = mapped_column(ForeignKey('cardapio.id'), primary_key = True)
    pedido: Mapped['Pedido'] = relationship(back_populates = 'associacao_cardapio')
    cardapio: Mapped['Cardapio'] = relationship(back_populates = 'associacao_pedido')

class PratoIngrediente(db.Model):
    __tablename__ = 'prato_ingrediente'
    id_prato: Mapped[int] = mapped_column(ForeignKey('prato.id'), primary_key = True)
    id_ingrediente: Mapped[int] = mapped_column(ForeignKey('ingrediente.id'), primary_key = True)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable = False)
    qtd: Mapped[float] = mapped_column(Numeric(6,2), nullable = False)
    prato: Mapped['Prato'] = relationship(back_populates = 'associacao_ingrediente')
    ingrediente: Mapped['Ingrediente'] = relationship(back_populates = 'associacao')

class PratoCategoria(db.Model):
    __tablename__ = 'prato_categoria'
    id_prato: Mapped[int] = mapped_column(ForeignKey('prato.id'), primary_key = True)
    id_categoria: Mapped[int] = mapped_column(ForeignKey('categoria.id'), primary_key = True)
    prato: Mapped['Prato'] = relationship(back_populates = 'associacao_categoria')
    categoria: Mapped['Categoria'] = relationship(back_populates = 'associacao_prato')
