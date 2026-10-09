#Arquivo às blueprints de autenticação 
#TODO: Inserir função de recuperar conta (email), Inserir login por oAuth (google), Adicionar MFA

import db
import validations as val
import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, request, jsonify
from utils import err_json, get_attr
from extensions import limiter

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth",__name__,url_prefix="/api")

@auth_bp.route('/login', methods=["POST"])
@limiter.limit("5 per minute")
def login():
    
    #O {}/"" é pra não crashar com empty req/not json
    data = request.get_json() or {}
    email = (data.get('email') or "").strip()
    password = (data.get('password') or "").strip()

    errors = {}

    if not email:
        print("Empty email from Json")
        errors['email'] = "Email é obrigatório"

    if not password:
        print("Empty password from Json")        
        errors['password'] = "Senha é obrigatória"

    if errors:
        logger.warning("Tentativa de login inválida: erros nas informações",email)
        return err_json("VALIDATION_FAILED","Por favor, arrume os erros abaixo",errors)

    database = db.get_db()
    user = database.execute("SELECT * FROM test_table WHERE u_email = ?",(email,)).fetchone()
    
    logger.info("Tentativa de login do email: %s", email)
    if not user:
        logger.warning("Tentativa de login inválida por %s: usuário inexistente",email)
        return err_json(
            code="INVALID_CREDENTIALS",
            message="Email ou senha incorreta",
            status = 401
        )

    stored_pwd = user["pwd_hash"]
    ph = PasswordHasher();

    try:
        ph.verify(stored_pwd,password)
    except VerifyMismatchError:
        logger.warning("Tentativa de login inválida por %s: senha incorreta",email)
        return err_json(
            code="INVALID_CREDENTIALS",
            message="Email ou senha incorreta",
            status = 401
        )        
    except Exception:
        logger.exception("Impossibilitado de realizar verificação do email: %s",email)
        return err_json(
            code="COULD_NOT_CHECK",
            message="Algo deu errado, tente novamente",
            status = 500
        ) 

    logger.info("Login realizado com sucesso por %s",email)
    #Vai ser usado pra ir pra próxima página
    return jsonify({
    "success":True,
    "user":{"email":user["u_email"]}
    }),200

@auth_bp.route('/cadastro', methods=["POST"])
def cadastro():
    data = request.get_json() or {}
    fields = ['name','surname','email','password','password_confirmation','cep','country','street','number','extra']
    f_info = get_attr(data,fields);
    database = db.get_db()
    missing = [k for k in fields if not f_info[k]]

    if missing:
        return err_json(
            code="MISSING_INFO",
            message="Há campos ausentes",
            fields=missing,
            status = 400
        )   

    if not val.check_email(f_info['email']):
        return err_json(
            code="INVALID_EMAIL",
            message="O email inserido é inválido.",
            status = 400
        )        

    if f_info['password'] != f_info['password_confirmation']:
        return err_json(
            code="PASSWORD_DOES_NOT_MATCH",
            message="Senhas inseridas são diferentes.",
            status = 409
        )
     
    if not val.check_pwd_strength(f_info['password']):
        return err_json(
            code="WEAK_PASSWORD",
            message="Senha muito fraca, utilize outra senha",
            status = 409
        ) 

    if val.check_user_exists(f_info['email']):
        return err_json(
            code="USER_EXISTS",
            message="Email já está registrado.",
            status = 401
        ) 
    ph = PasswordHasher();
    #depois trocar a tabela e os requisitos
    database.execute("INSERT INTO test_table (u_email,pwd_hash) VALUES (?,?)", 
    (f_info['email'], ph.hash(f_info['password']),)
    )
    database.commit()
    return jsonify({"message": "Usuário criado com sucesso"}), 201  