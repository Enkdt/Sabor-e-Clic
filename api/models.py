from datetime import datetime, date, time
from sqlalchemy import CheckConstraint, ForeignKey, String, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from extensions import db
from argon2 import PasswordHasher

# TODO: Terminar todas as tabelas
# TODO: Ligar isso a um banco de dados funcional
# TODO: Testar 0-0
# TODO: Depois ver onde deixar a função get_user, delete_user, etc

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(90), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    funcionario: Mapped['Funcionario | None'] = relationship(back_populates='usuario')
    cozinheiro: Mapped['Cozinheiro | None'] = relationship(back_populates='usuario')
    cliente: Mapped['Cliente | None'] = relationship(back_populates='usuario')

class Funcionario(db.Model):
    __tablename__ = 'funcionario'
    id_usuario: Mapped[int] = mapped_column(ForeignKey('usuario.id'), primary_key=True)
    nivel_permissao: Mapped[int] = mapped_column(nullable=False)
    usuario: Mapped['Usuario'] = relationship(back_populates='funcionario')
    __table_args__ = (
        CheckConstraint(
            "nivel_permissao BETWEEN 1 AND 5", # TODO: Ajustar isso
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
    pedidos: Mapped[list['Pedido']] = relationship(secondary='cozinheiro_pedido', back_populates='cozinheiros')
    associacao_pedido: Mapped[list['CozinheiroPedido']] = relationship(back_populates='cozinheiro')


class Turno(db.Model):
    __tablename__ = 'turno'
    id_cozinheiro: Mapped[int] = mapped_column(ForeignKey('cozinheiro.id_usuario'), primary_key=True)
    id_turno: Mapped[int] = mapped_column(primary_key=True)
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
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True) # numero que difere ele de outros enderecos
    rua: Mapped[str] = mapped_column(String(45), nullable=False)
    numero: Mapped[str] = mapped_column(String(5), nullable=False)
    complemento: Mapped[str| None] = mapped_column(String(45),nullable=True)
    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    pais: Mapped[str] = mapped_column(String(45), nullable=False)
    bairro: Mapped[str] = mapped_column(String(45), nullable=False)
    cidade: Mapped[str] = mapped_column(String(45), nullable=False)
    estado: Mapped[str] = mapped_column(String(3), nullable=False) # Estado seria: SP, RJ, MG, etc.
    cliente: Mapped['Cliente'] = relationship(back_populates='endereco')

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

class Cardapio(db.Model):
    __tablename__ = 'cardapio'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    prato: Mapped[list['Prato']] = relationship(back_populates='cardapio')
    pedidos: Mapped[list['Pedido']] = relationship(secondary='pedido_cardapio', back_populates='cardapios')
    associacao_pedido: Mapped[list['PedidoCardapio']] = relationship(back_populates='cardapio')

class Restaurante(db.Model):
    __tablename__ = 'restaurante'
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    # TODO: Fazer isso ser derivado
    receita_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    ticket_medio: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
     
    pedidos_total: Mapped[int] = mapped_column(nullable=False)
    vendas_total: Mapped[int] = mapped_column(nullable=False)
    itens_estoque: Mapped[int] = mapped_column(nullable=False)
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
    pedidos: Mapped[list['Pedido']] = relationship(secondary='pedido_prato', back_populates='pratos')
    associacao_pedido: Mapped[list['PedidoPrato']] = relationship(back_populates='prato')
    ingredientes: Mapped[list['Ingrediente']] = relationship(secondary='prato_ingrediente', back_populates='pratos')
    associacao_ingrediente: Mapped[list['PratoIngrediente']] = relationship(back_populates='prato')
    categorias: Mapped[list['Categoria']] = relationship(secondary='prato_categoria', back_populates='pratos')
    associacao_categoria: Mapped[list['PratoCategoria']] = relationship(back_populates='prato')

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    pratos: Mapped[list['Prato']] = relationship(secondary = 'prato_categoria', back_populates='categorias')
    associacao_prato: Mapped[list['PratoCategoria']] = relationship(back_populates = 'categoria')

class Ingrediente(db.Model):
    __tablename__ = 'ingrediente'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    validade: Mapped[date] = mapped_column(nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False) # Ex: KG, G, L, ML
    quantidade: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    pratos: Mapped[list['Prato']] = relationship(secondary='prato_ingrediente', back_populates='ingredientes')
    associacao: Mapped[list['PratoIngrediente']] = relationship(back_populates='ingrediente')

class Bancada(db.Model):
    __tablename__ = 'bancada'
    id: Mapped[int] = mapped_column(primary_key=True)
    agendamento: Mapped[list['Agendamento']] = relationship(back_populates='bancada')
    bancada_endereco: Mapped[list['BancadaEndereco']] = relationship(back_populates='bancada')
    bancada_horario_disponivel: Mapped[list['BancadaHorarioDisponivel']] = relationship(back_populates='bancada',cascade='all, delete-orphan')
    equipamentos: Mapped[list['Equipamento']] = relationship(secondary='bancada_equipamento', back_populates='bancadas')
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

class Agendamento(db.Model): # TODO: Fazer com que não possa ter agendamentos que se sobrepoem
    __tablename__ = 'agendamento'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cozinheiro: Mapped[int] = mapped_column(ForeignKey('cozinheiro.id_usuario'))
    id_bancada: Mapped[int] = mapped_column(ForeignKey('bancada.id'))
    horario_agendado: Mapped[datetime] = mapped_column(nullable=False)
    tempo_agendado: Mapped[int] = mapped_column(nullable=False)
    preco_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    cozinheiro: Mapped['Cozinheiro'] = relationship(back_populates='agendamento')
    bancada: Mapped['Bancada'] = relationship(back_populates='agendamento')

class Equipamento(db.Model):
    __tablename__ = 'equipamento'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    bancadas: Mapped[list['Bancada']] = relationship(secondary='bancada_equipamento', back_populates='equipamentos')
    associacao_bancada: Mapped[list['BancadaEquipamento']] = relationship(back_populates='equipamento')

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
    pedido: Mapped['Pedido'] = relationship(back_populates = 'associacao_prato')
    prato: Mapped['Prato'] = relationship(back_populates = 'associacao_pedido')

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

#
def get_user(email:str):
    return db.session.execute(db.select(Usuario).where(Usuario.email == email)).scalar_one_or_none()

def create_user(full_name: str,email: str,password: str,cep: str,country: str,street: str,
number: str,neighborhood: str,city: str,state: str,complement: str | None = None,):
    
    if get_user(email) is not None:
        raise ValueError("Email já está registrado.")

    ph = PasswordHasher()
    user = Usuario(nome=full_name,email=email,senha_hash=ph.hash(password),)
    
    cliente = Cliente(usuario=user)
    endereco = ClienteEndereco(rua=street,numero=number,complemento=complement,
    bairro=neighborhood,cidade=city,estado=state,cep=cep,pais=country,)
    cliente.endereco.append(endereco)

    try:
        db.session.add(cliente)
        db.session.commit()
        return user
    except Exception:
        db.session.rollback()
        raise