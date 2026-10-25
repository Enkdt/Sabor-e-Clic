from argon2 import PasswordHasher
from sqlalchemy.exc import IntegrityError

from extensions import db
from .usuario import *

ph = PasswordHasher()

class CRUD:
    class create:
        # usuario.py
        @staticmethod
        def funcionario(nome:str, email:str, senha:str, nivel_permissao:int):
            try:
                user = Usuario(nome=nome, email=email, senha_hash=ph.hash(senha))
                func = Funcionario(nivel_permissao=nivel_permissao, usuario=user)
                db.session.add(func)
                db.session.commit()
                return func
            
            except Exception:
                db.session.rollback()
                raise

        @staticmethod
        def cozinheiro(nome:str, email:str, senha:str, especialidade:str):
            try:
                user = Usuario(nome=nome, email=email, senha_hash=ph.hash(senha))
                cozi = Cozinheiro(usuario=user, especialidade=especialidade)
                db.session.add(cozi)
                db.session.commit()
                return cozi
            except Exception:
                db.session.rollback()
                raise

        @staticmethod
        def turno(id_cozinheiro:int, inicio, fim, periodo):
            try:
                turn = Turno(id_cozinheiro=id_cozinheiro, inicio=inicio, fim=fim, periodo=periodo)
                db.session.add(turn)
                db.session.commit()
                return turn
            except Exception:
                db.session.rollback()
                raise

        @staticmethod
        def cliente(nome:str, email:str, senha:str):
            try:
                user = Usuario(nome=nome, email=email, senha_hash=ph.hash(senha))
                clie = Cliente(usuario=user)
                db.session.add(clie)
                db.session.commit()
                return clie
            except Exception:
                db.session.rollback()
                raise

        @staticmethod
        def clienteEndereco(id_cliente:int, rua:str, numero:str, cep:str, pais:str, estado:str, cidade:str, bairro:str, complemento:str = None):
            try:
                ende = ClienteEndereco(id_cliente=id_cliente, rua=rua, numero=numero, complemento = complemento, cep=cep, pais=pais, estado=estado, cidade=cidade, bairro=bairro)
                db.session.add(ende)
                db.session.commit()
                return ende
            except Exception:
                db.session.rollback()
                raise

        # pedido.py
        
        # restaurante.py
        
        # bancada.py
        
        # associacao.py (não tenho certeza se precisamos)

    class read:
        pass
    class update:
        pass
    class delete:
        pass
    