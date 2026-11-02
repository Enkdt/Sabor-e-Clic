from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app import app
from models.crud import CRUD

DEMO_PASSWORD = "SaborDemo123!"

RESTAURANTS = [
    {
        "nome": "Cozinha Demo",
        "categoria": "Brasileira",
        "cardapio": "Almoço executivo",
        "nome_prato": "Prato feito brasileiro",
        "preco": Decimal("32.00"),
        "quantidade": 20,
        "endereco": {
            "rua": "Rua das Flores",
            "numero": "120",
            "complemento": "Loja 1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Arroz", "KG", "0.18"), ("Feijão", "KG", "0.12"), ("Carne bovina", "KG", "0.20")],
    },
    {
        "nome": "Padaria Demo",
        "categoria": "Padaria",
        "cardapio": "Pães e cafés",
        "nome_prato": "Pão na chapa com café",
        "preco": Decimal("9.50"),
        "quantidade": 20,
        "endereco": {
            "rua": "Rua do Comércio",
            "numero": "45",
            "complemento": "Loja 2",
            "bairro": "Centro",
            "cidade": "Campinas",
            "estado": "SP",
        },
        "ingredientes": [("Farinha de trigo", "KG", "0.25"), ("Leite", "L", "0.20"), ("Ovo", "UN", "2.00")],
    },
    {
        "nome": "Cantina Italiana Demo",
        "categoria": "Italiana",
        "cardapio": "Massas artesanais",
        "nome_prato": "Fettuccine ao molho sugo",
        "preco": Decimal("38.00"),
        "quantidade": 15,
        "endereco": {
            "rua": "Rua Itália",
            "numero": "80",
            "complemento": "Salão principal",
            "bairro": "Jardim Europa",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Farinha de trigo", "KG", "0.18"), ("Molho de tomate", "KG", "0.12"), ("Queijo", "KG", "0.08")],
    },
    {
        "nome": "Japastel Demo",
        "categoria": "Japonesa",
        "cardapio": "Combinados orientais",
        "nome_prato": "Combo sushi especial",
        "preco": Decimal("45.00"),
        "quantidade": 20,
        "endereco": {
            "rua": "Rua Japão",
            "numero": "210",
            "complemento": "Loja 3",
            "bairro": "Liberdade",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Arroz japonês", "KG", "0.18"), ("Salmão", "KG", "0.12"), ("Alga nori", "UN", "2.00")],
    },
    {
        "nome": "Taco Demo",
        "categoria": "Mexicana",
        "cardapio": "Tacos e burritos",
        "nome_prato": "Burrito mexicano",
        "preco": Decimal("27.00"),
        "quantidade": 25,
        "endereco": {
            "rua": "Rua México",
            "numero": "55",
            "complemento": "Loja 4",
            "bairro": "Centro",
            "cidade": "Santos",
            "estado": "SP",
        },
        "ingredientes": [("Tortilha", "UN", "2.00"), ("Feijão", "KG", "0.08"), ("Carne moída", "KG", "0.12")],
    },
    {
        "nome": "Garden Demo",
        "categoria": "Vegetariana",
        "cardapio": "Pratos naturais",
        "nome_prato": "Bowl de quinoa e legumes",
        "preco": Decimal("29.00"),
        "quantidade": 15,
        "endereco": {
            "rua": "Rua das Palmeiras",
            "numero": "300",
            "complemento": "Loja 5",
            "bairro": "Vila Verde",
            "cidade": "Campinas",
            "estado": "SP",
        },
        "ingredientes": [("Lentilha", "KG", "0.15"), ("Legumes variados", "KG", "0.18"), ("Quinoa", "KG", "0.10")],
    },
    {
        "nome": "Burger Demo",
        "categoria": "Hamburgueria",
        "cardapio": "Hambúrgueres especiais",
        "nome_prato": "Burger especial da casa",
        "preco": Decimal("34.90"),
        "quantidade": 20,
        "endereco": {
            "rua": "Avenida Central",
            "numero": "500",
            "complemento": "Loja 6",
            "bairro": "Jardins",
            "cidade": "São Paulo",
            "estado": "SP",
        },
        "ingredientes": [("Pão brioche", "UN", "1.00"), ("Carne bovina", "KG", "0.18"), ("Queijo", "KG", "0.03")],
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
        "especialidade": "Hambúrgueres e grelhados",
        "inicio": time(14, 0),
        "fim": time(22, 0),
        "periodo": "noturno",
    },
]

ORDERS = [
    {
        "customer": "ana.demo@sabor.test",
        "restaurant": "Cozinha Demo",
        "cook": "rafael.cozinha@sabor.test",
        "data": date(2026, 10, 29),
        "quantidade": 2,
        "status": "pronto",
        "tempo_estimado": 25,
    },
    {
        "customer": "bruno.demo@sabor.test",
        "restaurant": "Japastel Demo",
        "cook": "julia.ferraz@sabor.test",
        "data": date(2026, 10, 30),
        "quantidade": 1,
        "status": "preparando",
        "tempo_estimado": 35,
    },
    {
        "customer": "carla.demo@sabor.test",
        "restaurant": "Burger Demo",
        "cook": "marcos.nunes@sabor.test",
        "data": date(2026, 10, 31),
        "quantidade": 2,
        "status": "pronto",
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
    return get_or_create(
        CRUD.read.ingredientes,
        CRUD.create.ingrediente,
        {"nome": name},
        nome=name,
        validade=date.today() + timedelta(days=365),
        unidade=unit,
        quantidade=Decimal("50.00"),
    )


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


def ensure_bench(address, hourly_price):
    matching_addresses = CRUD.read.enderecos_bancada(filters={
        "rua": address["rua"],
        "numero": address["numero"],
    })

    if matching_addresses:
        bench = CRUD.read.bancada(matching_addresses[0].id_bancada)
        if Decimal(str(bench.preco_hora)) != hourly_price:
            CRUD.update.bancada(bench.id, {"preco_hora": hourly_price})
            bench = CRUD.read.bancada(bench.id)
    else:
        bench = CRUD.create.bancada(preco_hora=hourly_price)
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
    dishes = {}
    ingredients = {}

    for data in RESTAURANTS:
        restaurant = get_or_create(
            CRUD.read.restaurantes,
            CRUD.create.restaurante,
            {"nome": data["nome"]},
            nome=data["nome"],
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

        dishes[data["nome"]] = {
            "restaurant": restaurant,
            "menu": menu,
            "dish": dish,
            "price": data["preco"],
        }

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

    benches = [
        ensure_bench(bench_addresses[0], Decimal("40.00")),
        ensure_bench(bench_addresses[1], Decimal("45.00")),
    ]

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
