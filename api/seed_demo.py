from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app import app
from models.crud import CRUD
from utils import slugify
import placeholders

DEMO_PASSWORD = "SaborDemo123!"

# Paleta por índice para variar as fotos de demonstração.
_CORES = ["#426700", "#9a5b00", "#7a1f4b", "#1f5a7a", "#8a6d00", "#6a1f7a", "#2f7a3f"]


def _placeholder_image(texto, cor):
    """Gera uma imagem rotulada em uploads/ (via ImageMagick) para a demo.

    Delega para o módulo compartilhado `placeholders`. Devolve a chave ou None
    quando o `magick` não está disponível (ex.: Vercel/CI) — nesse caso o app
    serve o placeholder padrão estático automaticamente na serialização.
    """
    return placeholders.generate_labeled_placeholder(texto, cor)

RESTAURANTS = [
    {
        "nome": "Raiz Vegana",
        "categoria": "Brasileira",
        "cardapio": "Almoço plant-based",
        "nome_prato": "Prato feito de feijoada vegana",
        "preco": Decimal("32.00"),
        "quantidade": 20,
        "endereco": {
            "rua": "Rua das Flores",
            "numero": "120",
            "complemento": "Dark kitchen 1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Arroz integral", "KG", "0.18"), ("Feijão preto", "KG", "0.14"), ("Cogumelo paris", "KG", "0.12")],
        "extras": [("Feijoada vegana completa", Decimal("36.00")), ("Strogonoff de cogumelos", Decimal("30.00"))],
    },
    {
        "nome": "Pão & Grão Vegano",
        "categoria": "Padaria",
        "cardapio": "Pães e cafés veganos",
        "nome_prato": "Pão na chapa com café vegetal",
        "preco": Decimal("9.50"),
        "quantidade": 20,
        "endereco": {
            "rua": "Rua do Comércio",
            "numero": "45",
            "complemento": "Dark kitchen 2",
            "bairro": "Centro",
            "cidade": "Campinas",
            "estado": "SP",
        },
        "ingredientes": [("Farinha de trigo", "KG", "0.25"), ("Leite de aveia", "L", "0.20"), ("Margarina vegetal", "KG", "0.05")],
        "extras": [("Croissant de tofu defumado", Decimal("12.00")), ("Bolo de cenoura com cobertura de cacau", Decimal("8.00"))],
    },
    {
        "nome": "Cantina Verde",
        "categoria": "Italiana",
        "cardapio": "Massas artesanais veganas",
        "nome_prato": "Fettuccine ao molho sugo",
        "preco": Decimal("38.00"),
        "quantidade": 15,
        "endereco": {
            "rua": "Rua Itália",
            "numero": "80",
            "complemento": "Dark kitchen 3",
            "bairro": "Jardim Europa",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Farinha de sêmola", "KG", "0.18"), ("Molho de tomate", "KG", "0.14"), ("Queijo vegetal de castanha", "KG", "0.08")],
        "extras": [("Lasanha de berinjela", Decimal("42.00")), ("Nhoque ao pesto de manjericão", Decimal("35.00"))],
    },
    {
        "nome": "Oriente Vegano",
        "categoria": "Japonesa",
        "cardapio": "Combinados orientais veganos",
        "nome_prato": "Combo sushi vegano especial",
        "preco": Decimal("45.00"),
        "quantidade": 20,
        "endereco": {
            "rua": "Rua Japão",
            "numero": "210",
            "complemento": "Dark kitchen 4",
            "bairro": "Liberdade",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Arroz japonês", "KG", "0.18"), ("Pepino", "KG", "0.10"), ("Alga nori", "UN", "2.00")],
        "extras": [("Temaki de legumes", Decimal("28.00")), ("Yakisoba de tofu e shiitake", Decimal("33.00"))],
    },
    {
        "nome": "Taco Verde",
        "categoria": "Mexicana",
        "cardapio": "Tacos e burritos veganos",
        "nome_prato": "Burrito vegano",
        "preco": Decimal("27.00"),
        "quantidade": 25,
        "endereco": {
            "rua": "Rua México",
            "numero": "55",
            "complemento": "Dark kitchen 5",
            "bairro": "Centro",
            "cidade": "Santos",
            "estado": "SP",
        },
        "ingredientes": [("Tortilha de milho", "UN", "2.00"), ("Feijão carioca", "KG", "0.10"), ("Proteína de soja", "KG", "0.12")],
        "extras": [("Taco de jaca desfiada", Decimal("22.00")), ("Nachos com guacamole", Decimal("25.00"))],
    },
    {
        "nome": "Jardim Natural",
        "categoria": "Saudável",
        "cardapio": "Pratos naturais veganos",
        "nome_prato": "Bowl de quinoa e legumes",
        "preco": Decimal("29.00"),
        "quantidade": 15,
        "endereco": {
            "rua": "Rua das Palmeiras",
            "numero": "300",
            "complemento": "Dark kitchen 6",
            "bairro": "Vila Verde",
            "cidade": "Campinas",
            "estado": "SP",
        },
        "ingredientes": [("Lentilha", "KG", "0.15"), ("Legumes variados", "KG", "0.18"), ("Quinoa", "KG", "0.10")],
        "extras": [("Wrap vegano de grão-de-bico", Decimal("26.00")), ("Salada caesar vegana", Decimal("24.00"))],
    },
    {
        "nome": "Planta Burger",
        "categoria": "Hamburgueria",
        "cardapio": "Hambúrgueres vegetais",
        "nome_prato": "Burger vegetal da casa",
        "preco": Decimal("34.90"),
        "quantidade": 20,
        "endereco": {
            "rua": "Avenida Central",
            "numero": "500",
            "complemento": "Dark kitchen 7",
            "bairro": "Jardins",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Pão brioche vegano", "UN", "1.00"), ("Hambúrguer de grão-de-bico", "UN", "1.00"), ("Queijo vegetal", "KG", "0.03")],
        "extras": [("Duplo burger de feijão preto", Decimal("39.90")), ("Batata frita com cheddar vegetal", Decimal("22.00"))],
    },
]

CUSTOMERS = [
    {
        "nome": "Ana Clara Demo",
        "email": "ana.demo@sabor.test",
        "rua": "Rua dos Sabores",
        "numero": "101",
        "cep": "01000-000",
        "pais": "Brasil",
        "estado": "SP",
        "cidade": "São Paulo",
        "bairro": "Centro",
        "complemento": "Apto 12",
    },
    {
        "nome": "Bruno Lima Demo",
        "email": "bruno.demo@sabor.test",
        "rua": "Avenida das Palmeiras",
        "numero": "220",
        "cep": "13010-000",
        "pais": "Brasil",
        "estado": "SP",
        "cidade": "Campinas",
        "bairro": "Cambuí",
        "complemento": "Casa 2",
    },
    {
        "nome": "Carla Souza Demo",
        "email": "carla.demo@sabor.test",
        "rua": "Rua do Mercado",
        "numero": "53",
        "cep": "11010-000",
        "pais": "Brasil",
        "estado": "SP",
        "cidade": "Santos",
        "bairro": "Centro",
        "complemento": "Fundos",
    },
]

COOKS = [
    {
        "nome": "Rafael Cozinha Demo",
        "email": "rafael.cozinha@sabor.test",
        "especialidade": "Culinária brasileira",
        "inicio": time(8, 0),
        "fim": time(16, 0),
        "periodo": "matutino",
    },
    {
        "nome": "Julia Ferraz Demo",
        "email": "julia.ferraz@sabor.test",
        "especialidade": "Culinária oriental",
        "inicio": time(12, 0),
        "fim": time(20, 0),
        "periodo": "vespertino",
    },
    {
        "nome": "Marcos Nunes Demo",
        "email": "marcos.nunes@sabor.test",
        "especialidade": "Hambúrgueres vegetais",
        "inicio": time(14, 0),
        "fim": time(22, 0),
        "periodo": "noturno",
    },
]

ORDERS = [
    {
        "customer": "ana.demo@sabor.test",
        "restaurant": "Raiz Vegana",
        "cook": "rafael.cozinha@sabor.test",
        "data": date(2026, 10, 29),
        "quantidade": 2,
        "status": "pago",
        "metodo_pagamento": "entrega",
        "tempo_estimado": 25,
    },
    {
        "customer": "bruno.demo@sabor.test",
        "restaurant": "Oriente Vegano",
        "cook": "julia.ferraz@sabor.test",
        "data": date(2026, 10, 30),
        "quantidade": 1,
        "status": "preparando",
        "tempo_estimado": 35,
    },
    {
        "customer": "carla.demo@sabor.test",
        "restaurant": "Planta Burger",
        "cook": "marcos.nunes@sabor.test",
        "data": date(2026, 10, 31),
        "quantidade": 2,
        "status": "pago",
        "metodo_pagamento": "pix_entrega",
        "tempo_estimado": 20,
    },
]


def get_or_create(read, create, filters, **data):
    records = read(filters=filters)

    if records:
        return records[0]

    return create(**data)


def ensure_restaurant_address(restaurant, address):
    addresses = CRUD.read.enderecos_restaurante(filters={
        "id_restaurante": restaurant.id
    })

    if addresses:
        return addresses[0]

    return CRUD.create.restaurante_endereco(
        id_restaurante=restaurant.id,
        id=1,
        **address
    )


def ensure_customer(data):
    user = CRUD.read.usuario_por_email(data["email"])

    if user is None:
        user = CRUD.create.cliente_com_endereco(
            nome=data["nome"],
            email=data["email"],
            senha=DEMO_PASSWORD,
            rua=data["rua"],
            numero=data["numero"],
            cep=data["cep"],
            pais=data["pais"],
            estado=data["estado"],
            cidade=data["cidade"],
            bairro=data["bairro"],
            complemento=data["complemento"],
        )
    else:
        cliente = CRUD.read.cliente(user.id)
        if cliente is None:
            CRUD.create.cliente(id_usuario=user.id)

        addresses = CRUD.read.enderecos_cliente(filters={
            "id_usuario": user.id
        })
        if not addresses:
            CRUD.create.cliente_endereco(
                id_usuario=user.id,
                rua=data["rua"],
                numero=data["numero"],
                cep=data["cep"],
                pais=data["pais"],
                estado=data["estado"],
                cidade=data["cidade"],
                bairro=data["bairro"],
                complemento=data["complemento"],
            )

    if not user.email_verificado:
        user = CRUD.update.verificar_email(user.id)

    return user


def ensure_profile(role, data):
    user = CRUD.read.usuario_por_email(data["email"])

    if user is None:
        if role == "funcionario":
            profile = CRUD.create.funcionario(
                nome=data["nome"],
                email=data["email"],
                senha=DEMO_PASSWORD,
                nivel_permissao=data["nivel_permissao"],
            )
        else:
            profile = CRUD.create.cozinheiro(
                nome=data["nome"],
                email=data["email"],
                senha=DEMO_PASSWORD,
                especialidade=data["especialidade"],
            )
        user = profile.usuario
    else:
        profile_reader = CRUD.read.funcionario if role == "funcionario" else CRUD.read.cozinheiro
        profile = profile_reader(user.id)
        if profile is None:
            raise RuntimeError(
                f'O e-mail reservado para demonstração {data["email"]} já existe sem o perfil esperado.'
            )

    if not user.email_verificado:
        CRUD.update.verificar_email(user.id)

    return profile


def ensure_ingredient(name, unit):
    ing = get_or_create(
        CRUD.read.ingredientes,
        CRUD.create.ingrediente,
        {"nome": name},
        nome=name,
        validade=date.today() + timedelta(days=365),
        unidade=unit,
        quantidade=Decimal("50.00"),
    )
    if not ing.imagem:
        key = _placeholder_image(name, "#5a4a2a")
        if key:
            CRUD.update.ingrediente(ing.id, {"imagem": key})
            ing = CRUD.read.ingrediente(ing.id)
    return ing


def ensure_dish_ingredient(dish, ingredient, unit, quantity):
    links = CRUD.read.pratos_ingredientes(filters={
        "id_prato": dish.id,
        "id_ingrediente": ingredient.id,
    })

    if not links:
        CRUD.create.prato_ingrediente(
            id_prato=dish.id,
            id_ingrediente=ingredient.id,
            unidade_medida=unit,
            qtd=Decimal(quantity),
        )


def ensure_bench(address, hourly_price, id_restaurante=None):
    matching_addresses = CRUD.read.enderecos_bancada(filters={
        "rua": address["rua"],
        "numero": address["numero"],
    })

    if matching_addresses:
        bench = CRUD.read.bancada(matching_addresses[0].id_bancada)
        updates = {}
        if Decimal(str(bench.preco_hora)) != hourly_price:
            updates["preco_hora"] = hourly_price
        if id_restaurante is not None and bench.id_restaurante != id_restaurante:
            updates["id_restaurante"] = id_restaurante
        if updates:
            CRUD.update.bancada(bench.id, updates)
            bench = CRUD.read.bancada(bench.id)
    else:
        bench = CRUD.create.bancada(preco_hora=hourly_price, id_restaurante=id_restaurante)
        CRUD.create.bancada_endereco(
            id_bancada=bench.id,
            id=1,
            **address,
        )

    availabilities = CRUD.read.horarios_disponiveis_bancada(filters={
        "id_bancada": bench.id
    })
    if not availabilities:
        CRUD.create.bancada_horario_disponivel(
            id_bancada=bench.id,
            id=1,
            inicio=time(8, 0),
            fim=time(18, 0),
        )

    return bench


def ensure_bench_equipment(bench, equipment, quantity):
    links = CRUD.read.bancadas_equipamentos(filters={
        "id_bancada": bench.id,
        "id_equipamento": equipment.id,
    })

    if not links:
        CRUD.create.bancada_equipamento(
            id_bancada=bench.id,
            id_equipamento=equipment.id,
            qtd=quantity,
        )


def ensure_booking(bench, cook, hour):
    bookings = CRUD.read.agendamentos(filters={"id_bancada": bench.id})

    if any(booking.id_cozinheiro == cook.id_usuario for booking in bookings):
        return

    duration = 120
    start_date = date.today() + timedelta(days=14)

    for day_offset in range(31):
        start = datetime.combine(start_date + timedelta(days=day_offset), hour)
        end = start + timedelta(minutes=duration)
        overlaps = any(
            start < booking.horario_agendado + timedelta(minutes=booking.tempo_agendado)
            and booking.horario_agendado < end
            for booking in bookings
        )

        if not overlaps:
            CRUD.create.agendamento(
                id_cozinheiro=cook.id_usuario,
                id_bancada=bench.id,
                horario_agendado=start,
                tempo_agendado=duration,
                preco_total=Decimal(str(bench.preco_hora)) * duration / 60,
            )
            return

    raise RuntimeError(f"Não foi encontrado horário livre para a bancada {bench.id}.")


def ensure_order(order_data, customers, cooks, dishes):
    customer = customers[order_data["customer"]]
    cook = cooks[order_data["cook"]]
    dish_data = dishes[order_data["restaurant"]]
    dish = dish_data["dish"]
    menu = dish_data["menu"]
    quantity = order_data["quantidade"]
    unit_price = dish_data["price"]
    total = unit_price * quantity

    orders = CRUD.read.pedidos(filters={
        "id_cliente": customer.id,
        "data": order_data["data"],
    })

    if orders:
        order = orders[0]
    else:
        order = CRUD.create.pedido(
            id_cliente=customer.id,
            data=order_data["data"],
            total=total,
            status=order_data["status"],
            tempo_estimado=order_data["tempo_estimado"],
            metodo_pagamento=order_data.get("metodo_pagamento"),
        )

    order_dishes = CRUD.read.pedidos_pratos(filters={
        "id_pedido": order.id,
        "id_prato": dish.id,
    })
    if not order_dishes:
        CRUD.create.pedido_prato(
            id_pedido=order.id,
            id_prato=dish.id,
            qtd=quantity,
            preco_und=unit_price,
            preco_total=total,
        )

    order_menus = CRUD.read.pedidos_cardapios(filters={
        "id_pedido": order.id,
        "id_cardapio": menu.id,
    })
    if not order_menus:
        CRUD.create.pedido_cardapio(
            id_pedido=order.id,
            id_cardapio=menu.id,
        )

    order_cooks = CRUD.read.cozinheiros_pedidos(filters={
        "id_pedido": order.id,
        "id_cozinheiro": cook.id_usuario,
    })
    if not order_cooks:
        CRUD.create.cozinheiro_pedido(
            id_pedido=order.id,
            id_cozinheiro=cook.id_usuario,
        )


def seed():
    # SEC-004: o seed de demonstração NUNCA roda em produção, mesmo chamado como
    # função (não só via main()). Usa o app ativo no contexto, com fallback ao global.
    try:
        from flask import current_app
        environment = current_app.config.get("ENVIRONMENT")
    except Exception:
        environment = app.config.get("ENVIRONMENT")
    if environment in {"production", "prod"}:
        raise RuntimeError("O seed de demonstração não pode ser executado em produção.")

    dishes = {}
    ingredients = {}

    for data in RESTAURANTS:
        restaurant = get_or_create(
            CRUD.read.restaurantes,
            CRUD.create.restaurante,
            {"nome": data["nome"]},
            nome=data["nome"],
            slug=slugify(data["nome"]),
        )
        ensure_restaurant_address(restaurant, data["endereco"])

        category = get_or_create(
            CRUD.read.categorias,
            CRUD.create.categoria,
            {"nome": data["categoria"]},
            nome=data["categoria"],
        )
        CRUD.create.restaurante_categoria(
            id_restaurante=restaurant.id,
            id_categoria=category.id,
        )

        menu = get_or_create(
            CRUD.read.cardapios,
            CRUD.create.cardapio,
            {"nome": data["cardapio"], "tipo": "demonstração"},
            nome=data["cardapio"],
            tipo="demonstração",
        )

        products = CRUD.read.pratos(filters={
            "id_restaurante": restaurant.id,
            "id_cardapio": menu.id,
        })
        if products:
            dish = products[0]
            CRUD.update.prato(dish.id, {
                "nome": data["nome_prato"],
                "preco_unidade": data["preco"],
                "quantidade": data["quantidade"],
            })
        else:
            dish = CRUD.create.prato(
                id_restaurante=restaurant.id,
                id_cardapio=menu.id,
                nome=data["nome_prato"],
                preco_unidade=data["preco"],
                quantidade=data["quantidade"],
            )

        dish_categories = CRUD.read.pratos_categorias(filters={
            "id_prato": dish.id,
            "id_categoria": category.id,
        })
        if not dish_categories:
            CRUD.create.prato_categoria(
                id_prato=dish.id,
                id_categoria=category.id,
            )

        for ingredient_name, unit, amount in data["ingredientes"]:
            ingredient_key = (ingredient_name, unit)
            if ingredient_key not in ingredients:
                ingredients[ingredient_key] = ensure_ingredient(ingredient_name, unit)
            ensure_dish_ingredient(
                dish,
                ingredients[ingredient_key],
                unit,
                amount,
            )

        # Pratos adicionais para que cada restaurante tenha >= 3 opções no cardápio.
        for extra_nome, extra_preco in data.get("extras", []):
            extras_existentes = CRUD.read.pratos(filters={
                "id_restaurante": restaurant.id,
                "id_cardapio": menu.id,
                "nome": extra_nome,
            })
            if extras_existentes:
                extra_dish = extras_existentes[0]
            else:
                extra_dish = CRUD.create.prato(
                    id_restaurante=restaurant.id,
                    id_cardapio=menu.id,
                    nome=extra_nome,
                    preco_unidade=extra_preco,
                    quantidade=15,
                )
            # Vincula os mesmos ingredientes do prato principal, para a seção nunca ficar vazia.
            for ingredient_name, unit, amount in data["ingredientes"]:
                ingredient_key = (ingredient_name, unit)
                if ingredient_key not in ingredients:
                    ingredients[ingredient_key] = ensure_ingredient(ingredient_name, unit)
                ensure_dish_ingredient(extra_dish, ingredients[ingredient_key], unit, amount)

        dishes[data["nome"]] = {
            "restaurant": restaurant,
            "menu": menu,
            "dish": dish,
            "price": data["preco"],
        }

        # Fotos de demonstração (geradas localmente) para restaurante e seus pratos, se ainda não têm.
        cor = _CORES[(restaurant.id - 1) % len(_CORES)]
        if not restaurant.imagem:
            key = _placeholder_image(restaurant.nome, cor)
            if key:
                CRUD.update.restaurante(restaurant.id, {"imagem": key})
        for prato in CRUD.read.pratos(filters={"id_restaurante": restaurant.id}):
            if not prato.imagem:
                key = _placeholder_image(prato.nome, cor)
                if key:
                    CRUD.update.prato(prato.id, {"imagem": key})

    customers = {
        data["email"]: ensure_customer(data)
        for data in CUSTOMERS
    }

    ensure_profile("funcionario", {
        "nome": "Admin Demo",
        "email": "admin.demo@sabor.test",
        "nivel_permissao": 5,
    })

    cooks = {}
    for data in COOKS:
        cook = ensure_profile("cozinheiro", data)
        cooks[data["email"]] = cook

        shifts = CRUD.read.turnos(filters={
            "id_cozinheiro": cook.id_usuario,
            "inicio": data["inicio"],
            "fim": data["fim"],
            "periodo": data["periodo"],
        })
        if not shifts:
            CRUD.create.turno(
                id_cozinheiro=cook.id_usuario,
                inicio=data["inicio"],
                fim=data["fim"],
                periodo=data["periodo"],
            )

    for order_data in ORDERS:
        ensure_order(order_data, customers, cooks, dishes)

    # Filia cada cozinheiro demo a um restaurante (round-robin), para que a tela do cozinheiro
    # tenha dados reais de gestão de pratos. Idempotente (a associação já evita duplicatas).
    restaurantes = CRUD.read.restaurantes()
    cooks_list = list(cooks.values())
    if restaurantes and cooks_list:
        for i, restaurante in enumerate(restaurantes):
            cook = cooks_list[i % len(cooks_list)]
            CRUD.create.cozinheiro_restaurante(cook.id_usuario, restaurante.id)

    bench_addresses = [
        {
            "rua": "Rua das Cozinhas Demo",
            "numero": "101",
            "complemento": "Bancada de preparo 1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        {
            "rua": "Rua das Cozinhas Demo",
            "numero": "102",
            "complemento": "Bancada de preparo 2",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
        },
    ]

    # SEC-002: as bancadas de demonstração pertencem aos dois primeiros
    # restaurantes; e os cozinheiros que fazem os agendamentos são filiados a eles,
    # de modo que o fluxo de aceitar/negar funcione respeitando a propriedade.
    demo_restaurantes = sorted(CRUD.read.restaurantes(), key=lambda r: r.id)
    rest_bancada_1 = demo_restaurantes[0] if demo_restaurantes else None
    rest_bancada_2 = demo_restaurantes[1] if len(demo_restaurantes) > 1 else rest_bancada_1

    benches = [
        ensure_bench(bench_addresses[0], Decimal("40.00"),
                     id_restaurante=rest_bancada_1.id if rest_bancada_1 else None),
        ensure_bench(bench_addresses[1], Decimal("45.00"),
                     id_restaurante=rest_bancada_2.id if rest_bancada_2 else None),
    ]

    # Filia os cozinheiros que fazem os agendamentos de demonstração às bancadas.
    if rest_bancada_1 is not None:
        CRUD.create.cozinheiro_restaurante(
            cooks["rafael.cozinha@sabor.test"].id_usuario, rest_bancada_1.id
        )
    if rest_bancada_2 is not None:
        CRUD.create.cozinheiro_restaurante(
            cooks["julia.ferraz@sabor.test"].id_usuario, rest_bancada_2.id
        )

    equipment_data = [
        ("Forno industrial", "Cocção", 1),
        ("Fogão industrial", "Cocção", 2),
        ("Batedeira", "Preparo", 1),
    ]
    equipment = []
    for name, kind, quantity in equipment_data:
        item = get_or_create(
            CRUD.read.equipamentos,
            CRUD.create.equipamento,
            {"nome": name, "tipo": kind},
            nome=name,
            tipo=kind,
        )
        equipment.append((item, quantity))

    for bench in benches:
        for item, quantity in equipment:
            ensure_bench_equipment(bench, item, quantity)

    ensure_booking(
        benches[0],
        cooks["rafael.cozinha@sabor.test"],
        time(9, 0),
    )
    ensure_booking(
        benches[1],
        cooks["julia.ferraz@sabor.test"],
        time(13, 0),
    )

    print("Seed de demonstração concluído.")
    print(f"Restaurantes: {len(CRUD.read.restaurantes())}")
    print(f"Clientes: {len(CRUD.read.clientes())}")
    print(f"Cozinheiros: {len(CRUD.read.cozinheiros())}")
    print(f"Pedidos: {len(CRUD.read.pedidos())}")
    print(f"Bancadas: {len(CRUD.read.bancadas())}")


def main():
    if app.config.get("ENVIRONMENT") in {"production", "prod"}:
        raise RuntimeError("O seed de demonstração não pode ser executado em produção.")

    with app.app_context():
        seed()


if __name__ == "__main__":
    main()
