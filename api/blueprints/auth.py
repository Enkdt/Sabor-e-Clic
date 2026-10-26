#Arquivo às blueprints de autenticação 
#TODO: Inserir função de recuperar conta (email), Inserir login por oAuth (google), Adicionar MFA
#TODO: inserir flaskJWT para validar a sessão
#Antes da produção, mudar a criação de user pro cep não ficar none
import validations as val
import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Blueprint, request, jsonify
from utils import err_json, get_attr, validateToken, sendAuthEmail
from extensions import db, limiter
from models.crud import CRUD


logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth",__name__,url_prefix="/api")

@auth_bp.route('/login', methods=["POST"])
@limiter.limit("5 per minute")
def login():
    
    #O {}/"" é pra não crashar com empty req/not json
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json(
                code="INVALID_JSON",
                message="Envie os dados em formato JSON válido.",
                status=400
        )

    email = (data.get('email') or "").strip()
    password = data.get('password') or ""

    errors = {}

    if not email:
        errors['email'] = "Email é obrigatório"

    if not password:
        errors['password'] = "Senha é obrigatória"

    if errors:
        logger.warning("Tentativa de login inválida: erros nas informações de %s",email)
        return err_json(
            code="VALIDATION_FAILED",
            message="Por favor, corrija os erros abaixo.",
            fields=errors,
            status=400
        )
    #Trocar pra get_user
    #user = database.execute("SELECT * FROM test_table WHERE u_email = ?",(email,)).fetchone()
    user = CRUD.read.cliente(email)

    logger.info("Tentativa de login do email: %s", email)
    if not user:
        logger.warning("Tentativa de login inválida por %s: usuário inexistente",email)
        return err_json(
            code="INVALID_CREDENTIALS",
            message="Email ou senha incorreta",
            status = 401
        )

    stored_pwd = user.senha_hash
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
    #Tem q ver da autenticação, cookies p validar
    return jsonify({
    "success":True,
    "user":{"email":user.email}
    }),200

@auth_bp.route('/cadastro', methods=["POST"])
def cadastro():
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json(
                code="INVALID_JSON",
                message="Envie os dados em formato JSON válido.",
                status=400
        )
    fields = ['name', 'surname', 'email', 'password','password_confirmation', 'cep', 'country',
    'street', 'number','neighborhood','city', 'state', 'extra']   
    f_info = get_attr(data,fields);
    required = [field for field in fields if field != 'extra']

    #REMOVER DEPOIS
    f_info['cep'] = '12345'
    f_info['neighborhood'] = '12345'

    missing = [field for field in required if not f_info.get(field)]
    if missing:
        return err_json(
            code="MISSING_INFO",
            message="Há campos ausentes",
            fields=missing,
            status = 400
        )   
    f_info["email"] = f_info["email"].strip()

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

    infos = [f_info[field] for field in required if field not in ('password','password_confirmation')]
    print(infos)
    if not val.check_pwd_strength(f_info['password'],infos):
        return err_json(
            code="WEAK_PASSWORD",
            message="Senha muito fraca, utilize outra senha",
            status = 409
        ) 

    try:
        user = CRUD.create.cliente(
            nome=f"{f_info['name']} {f_info['surname']}",
            email=f_info['email'].strip(),
            senha=f_info['password']
        )
        print(f'id: {CRUD.read.cliente(f_info['email'])}')
        userAddr = CRUD.create.clienteEndereco(
            id_cliente=CRUD.read.cliente(f_info['email']).id,
            rua=f_info['street'], 
            numero=f_info['number'],
            cep=f_info['cep'],
            pais=f_info['country'],
            estado=f_info['state'],
            cidade=f_info['city'],
            bairro=f_info['neighborhood'],
            complemento=f_info.get('extra') or None
        )
    except ValueError:
        logger.warning("Tentativa de criação de usuário com email já registrado")
        return err_json(
            code="USER_EXISTS",
            message="Email já está registrado.",
            status=409
        )    
    except IntegrityError:
        logger.warning("Conflito de integridade durante o cadastro")
        return err_json(
            code="INTEGRITY_ERROR",
            message="Não foi possível cadastrar os dados informados.",
            status=409
        )
    except SQLAlchemyError:
        logger.exception("Erro no banco durante o cadastro")
        return err_json(
            code="DATABASE_ERROR",
            message="Não foi possível criar a conta.",
            status=500
        )
    logger.info("Usuário %s registrado com sucesso",f_info['email'])
    sendAuthEmail(f_info['email'])
    return jsonify({
        "success": True,
        "message": "Usuário criado com sucesso",
        "user": {"email": f_info['email']}
    }), 201        

@auth_bp.route('/cadastro/validar', methods=["POST"])
def validar():
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json(
                code="INVALID_JSON",
                message="Envie os dados em formato JSON válido.",
                status=400
        )

    token = (data.get('token') or "").strip()
    if not token:
        return err_json(
                code="ABSENT_TOKEN",
                message="Nenhum token foi enviado",
                status=400
        )

    email = validateToken(token, "user validation")
    if not email:
        return err_json(
            code="INVALID_OR_EXPIRED_TOKEN",
            message="O link de validação é inválido ou expirou. Solicite um novo email.",
            status=400
        )

    user = CRUD.read.cliente(email)
    if not user:
        return err_json(
            code="USER_NOT_FOUND",
            message="Não foi encontrada uma conta para este token.",
            status=404
        )

    if not user.email_verificado:
        user.email_verificado = True
        db.session.commit()

    return jsonify({
        "success": True,
        "message": "Email validado com sucesso.",
        "user": {"email": user.email}
    }), 200

