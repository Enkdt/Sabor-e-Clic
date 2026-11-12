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
    slug: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)
    receita_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False, default=0)
    ticket_medio: Mapped[float] = mapped_column(Numeric(10,2), nullable=False, default=0)
    pedidos_total: Mapped[int] = mapped_column(nullable=False, default=0)
    vendas_total: Mapped[int] = mapped_column(nullable=False, default=0)
    itens_estoque: Mapped[int] = mapped_column(nullable=False, default=0)
    imagem: Mapped[str | None] = mapped_column(String(100), nullable=True)
    categorias: Mapped[list['Categoria']] = relationship(secondary=restaurante_categoria, back_populates='restaurantes')
    cozinheiros: Mapped[list['Cozinheiro']] = relationship(secondary='cozinheiro_restaurante', back_populates='restaurantes')
    prato: Mapped[list['Prato']] = relationship(back_populates='restaurante')
    restaurante_endereco: Mapped[list['RestauranteEndereco']] = relationship(back_populates='restaurante')
    bancadas: Mapped[list['Bancada']] = relationship(back_populates='restaurante')

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
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(70), nullable=True)
    preco_unidade: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    # DATA-003: `quantidade` NÃO é estoque consumível; o prato é uma "receita"
    # cuja disponibilidade é controlada por `disponivel` (liga/desliga pelo
    # cozinheiro do restaurante dono, ou admin). Nenhum pedido decrementa estoque.
    quantidade: Mapped[int] = mapped_column(nullable=False)
    disponivel: Mapped[bool] = mapped_column(nullable=False, default=True)
    descricao: Mapped[str | None] = mapped_column(String(300), nullable=True)
    imagem: Mapped[str | None] = mapped_column(String(100), nullable=True)
    restaurante: Mapped['Restaurante'] = relationship(back_populates='prato')
    cardapio: Mapped['Cardapio'] = relationship(back_populates='prato')
    associacao_pedido: Mapped[list['PedidoPrato']] = relationship(back_populates='prato')
    associacao_ingrediente: Mapped[list['PratoIngrediente']] = relationship(back_populates='prato')
    associacao_categoria: Mapped[list['PratoCategoria']] = relationship(back_populates='prato')

# Restaurantes e pratos usam as mesmas categorias; avaliar depois se vale separá-las.
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
    unidade: Mapped[str] = mapped_column(String(10), nullable=False) # Exemplos: KG, G, L e ML.
    quantidade: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    imagem: Mapped[str | None] = mapped_column(String(100), nullable=True)
    associacao: Mapped[list['PratoIngrediente']] = relationship(back_populates='ingrediente')
