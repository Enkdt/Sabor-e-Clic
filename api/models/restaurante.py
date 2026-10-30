from datetime import date
from sqlalchemy import ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db

restaurante_categoria = db.Table(
    'restaurante_categoria',
    db.Column('id_restaurante', ForeignKey('restaurante.id'), primary_key=True),
    db.Column('id_categoria', ForeignKey('categoria.id'), primary_key=True),
)

class Cardapio(db.Model):
    __tablename__ = 'cardapio'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    prato: Mapped[list['Prato']] = relationship(back_populates='cardapio')
    associacao_pedido: Mapped[list['PedidoCardapio']] = relationship(back_populates='cardapio')

class Restaurante(db.Model):
    __tablename__ = 'restaurante'
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    receita_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False, default=0)
    ticket_medio: Mapped[float] = mapped_column(Numeric(10,2), nullable=False, default=0)
    pedidos_total: Mapped[int] = mapped_column(nullable=False, default=0)
    vendas_total: Mapped[int] = mapped_column(nullable=False, default=0)
    itens_estoque: Mapped[int] = mapped_column(nullable=False, default=0)
    categorias: Mapped[list['Categoria']] = relationship(secondary=restaurante_categoria, back_populates='restaurantes')
    prato: Mapped[list['Prato']] = relationship(back_populates='restaurante')
    restaurante_endereco: Mapped[list['RestauranteEndereco']] = relationship(back_populates='restaurante')

class RestauranteEndereco(db.Model):
    __tablename__ = 'restaurante_endereco'
    id_restaurante: Mapped[int] = mapped_column(ForeignKey('restaurante.id'), primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    rua: Mapped[str] = mapped_column(String(45), nullable=False)
    numero: Mapped[str] = mapped_column(String(5), nullable=False)
    complemento: Mapped[str] = mapped_column(String(45))
    bairro: Mapped[str] = mapped_column(String(45), nullable=False)
    cidade: Mapped[str] = mapped_column(String(45), nullable=False)
    estado: Mapped[str] = mapped_column(String(3), nullable=False)
    restaurante: Mapped['Restaurante'] = relationship(back_populates='restaurante_endereco')

class Prato(db.Model):
    __tablename__ = 'prato'
    id: Mapped[int] = mapped_column(primary_key=True)
    id_restaurante: Mapped[int] = mapped_column(ForeignKey('restaurante.id'))
    id_cardapio: Mapped[int] = mapped_column(ForeignKey('cardapio.id'))
    preco_unidade: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    quantidade: Mapped[int] = mapped_column(nullable=False)
    restaurante: Mapped['Restaurante'] = relationship(back_populates='prato')
    cardapio: Mapped['Cardapio'] = relationship(back_populates='prato')
    associacao_pedido: Mapped[list['PedidoPrato']] = relationship(back_populates='prato')
    associacao_ingrediente: Mapped[list['PratoIngrediente']] = relationship(back_populates='prato')
    associacao_categoria: Mapped[list['PratoCategoria']] = relationship(back_populates='prato')

# Restaurante e pratos usam as mesmas categorias, ver dps se compensa separar em categoriaPrato e categoriaRestaurante
class Categoria(db.Model):
    __tablename__ = 'categoria'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    associacao_prato: Mapped[list['PratoCategoria']] = relationship(back_populates = 'categoria')
    restaurantes: Mapped[list['Restaurante']] = relationship(secondary=restaurante_categoria, back_populates='categorias')

class Ingrediente(db.Model):
    __tablename__ = 'ingrediente'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    validade: Mapped[date] = mapped_column(nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False) # Ex: KG, G, L, ML
    quantidade: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    associacao: Mapped[list['PratoIngrediente']] = relationship(back_populates='ingrediente')
