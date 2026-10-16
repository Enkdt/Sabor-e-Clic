# TODO: Ligar isso a um banco de dados funcional
# TODO: Testar 0-0

# Evita erro de Circular Import
from .usuario import (
    Usuario,
    Funcionario,
    Cozinheiro,
    Turno,
    Cliente,
    ClienteEndereco,
)

from .pedido import Pedido

from .restaurante import (
    Cardapio,
    Restaurante,
    RestauranteEndereco,
    Prato,
    Categoria,
    Ingrediente,
)

from .bancada import (
    Agendamento,
    Bancada,
    BancadaEndereco,
    BancadaHorarioDisponivel,
    Equipamento,
)

from .associacao import (
    CozinheiroPedido,
    BancadaEquipamento,
    PedidoPrato,
    PedidoCardapio,
    PratoIngrediente,
    PratoCategoria,
)