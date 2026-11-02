# Tests e funções vitais, depois separar em outrros arquivos

import sys
from getpass import getpass

from app import app
from utils import sendAuthEmail
from models.crud import CRUD
from sqlalchemy.exc import SQLAlchemyError


def enviar_email():
    recipient = input("E-mail do destinatário: ").strip()
    if not recipient:
        print("Erro: informe um e-mail.")
        return

    sendAuthEmail(recipient)
    print("E-mail de verificação enviado")


def criar_admin():
    print("\nCriar admin")
    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip()
    senha = getpass("Senha: ")
    confirmacao = getpass("Confirme a senha: ")

    if not nome or not email or not senha:
        print("Erro: todos os campos são obrigatórios.")
        return
    if senha != confirmacao:
        print("Erro: as senhas não coincidem.")
        return

    try:
        nivel = int(input("Nível de permissão (1–5): "))
        if nivel not in range(1, 6):
            raise ValueError
    except ValueError:
        print("Erro: o nível deve ser um número entre 1 e 5.")
        return

    funcionario = CRUD.create.funcionario(
        nome=nome,
        email=email,
        senha=senha,
        nivel_permissao=nivel
    )

    print("\nAdministrador criado")
    print(f"ID: {funcionario.id_usuario}")
    print(f"Nome: {nome}")
    print(f"E-mail: {email}")
    print(f"Nível de permissão: {nivel}")


def criar_restaurante():
    print("\nCriar restaurante")
    nome = input("Nome do restaurante: ").strip()
    categorias_input = input("Categorias(separadas por vírgula): ")

    categorias = list(dict.fromkeys(
        categoria.strip()
        for categoria in categorias_input.split(",")
        if categoria.strip()
    ))

    if not nome or len(nome) > 30:
        print("Erro: informe um nome de até 30 caracteres.")
        return

    if not categorias:
        print("Erro: informe ao menos uma categoria.")
        return

    if any(len(categoria) > 30 for categoria in categorias):
        print("Erro: cada categoria deve ter no máximo 30 caracteres.")
        return

    restaurante = CRUD.create.restaurante(nome=nome)
    categorias_criadas = []
    categorias_existentes = []

    for nome_categoria in categorias:
        existentes = CRUD.read.categorias(
            filters={"nome": nome_categoria},
            limit=1
        )

        if existentes:
            categoria = existentes[0]
            categorias_existentes.append(categoria.nome)
        else:
            categoria = CRUD.create.categoria(nome=nome_categoria)
            categorias_criadas.append(categoria.nome)

        CRUD.create.restaurante_categoria(
            id_restaurante=restaurante.id,
            id_categoria=categoria.id
        )

    print("\nRestaurante criado")
    print(f"ID: {restaurante.id}")
    print(f"Nome: {restaurante.nome}")
    print(f"Categorias criadas: {categorias_criadas}")
    print(f"Categorias reutilizadas: {categorias_existentes}")


def main():
    print("\nTESTES BIZARROS")
    print("1 - Enviar e-mail de verificação")
    print("2 - Criar administrador")
    print("3 - Criar restaurante")
    print("0 - Sair")

    opcao = input("\nSelecione uma opção: ").strip()

    if opcao == "0":
        print("seu monstro")
        return 0

    operacoes = {
        "1": enviar_email,
        "2": criar_admin,
        "3": criar_restaurante
    }

    if opcao not in operacoes:
        print("Opção inválida")
        return 1

    try:
        with app.app_context():
            operacoes[opcao]()

    except SQLAlchemyError:
        print("\nErro ao executar operação no banco de dados")
        return 1
    except ValueError as e:
        print(f"\nErro: {e}")
        return 1
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
