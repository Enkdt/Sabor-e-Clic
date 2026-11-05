# TODO: Conectar isso a um banco de dados funcional (neon).
# TODO: Testar de ponta a ponta.

# Evita erro de importação circular.
from .usuario import (
    Usuario,
    Funcionario,
    Cozinheiro,
    Turno,
    Cliente,
    ClienteEndereco,
    ClienteFavorito,
    PasswordResetToken,
    cozinheiro_restaurante,
)

from .pedido import Pedido, Avaliacao

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
