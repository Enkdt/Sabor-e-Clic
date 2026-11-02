# Arquivo das rotas de autenticação.
# TODO: Adicionar recuperação de conta por e-mail, login OAuth do Google e autenticação multifator.
# Antes da produção, garantir que o CEP seja informado ao criar uma conta.
import validations as val
import logging
import hashlib
import secrets
from threading import Thread
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from flask import Blueprint, request, jsonify, session, g, current_app
from flask_wtf.csrf import generate_csrf
from utils import err_json, get_attr, validateToken, sendAuthEmail, sendEmail
from extensions import db, limiter
from models.crud import CRUD
from models import Usuario
from decorators import user_role, validar
from models.usuario import PasswordResetToken


logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth",__name__,url_prefix="/api")


def _send_password_reset_email(app, recipient, raw_token):
    with app.app_context():
        link = f"{app.config['FRONTEND_BASE_URL'].rstrip('/')}/redefinir-senha?token={raw_token}"
        try:
            sendEmail(
                "Redefinição de senha - Sabor & Clic",
                recipient,
                f"Use este link para definir uma nova senha: {link}",
                f'<p><a href="{link}">Definir nova senha</a></p>',
            )
        except Exception:
            logger.exception("Falha ao enviar email de redefinição de senha")
            

@auth_bp.get('/csrf-token')
def csrf_token():
    return jsonify({"csrf_token": generate_csrf()}), 200


@auth_bp.route('/login', methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json(silent=True)
    if not val.check_json(data):
        logger.warning("Tentativa de login recusada por conteúdo JSON inválido.")
        return err_json(
                code="INVALID_JSON",
                message="Envie os dados em formato JSON válido.",
                status=400
        )

    email_input = data.get('email')
    email = email_input.strip() if isinstance(email_input, str) else ""
    password_input = data.get('password')
    password = password_input if isinstance(password_input, str) else ""

    errors = {}

    if not email:
        errors['email'] = "Email é obrigatório"

    if not password:
        errors['password'] = "Senha é obrigatória"

    if errors:
        logger.warning("Tentativa de login recusada por campos obrigatórios ausentes.")
        return err_json(
            code="VALIDATION_FAILED",
            message="Por favor, corrija os erros abaixo.",
            fields=errors,
            status=400
        )
    user = CRUD.read.usuario_por_email(email)

    if not user:
        logger.warning("Tentativa de login recusada: conta não encontrada.")
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
        logger.warning("Tentativa de login recusada: credenciais inválidas.")
        return err_json(
            code="INVALID_CREDENTIALS",
            message="Email ou senha incorreta",
            status = 401
        )        
    except (VerificationError, InvalidHashError):
        logger.exception("Falha ao verificar credenciais de acesso.")
        return err_json(
            code="COULD_NOT_CHECK",
            message="Algo deu errado, tente novamente",
            status = 500
        ) 

    if not user.email_verificado:
        logger.info("Login bloqueado porque o e-mail ainda não foi verificado.")
        return err_json(
            code="EMAIL_NOT_VERIFIED",
            message="Verifique seu email antes de entrar.",
            status=403
        )

    role = user_role(user)
    if role is None:
        logger.warning("Login recusado: conta sem um papel válido.")
        return err_json("INVALID_ACCOUNT_ROLE", "A conta não possui um perfil válido", status=403)
    session.clear()
    session["user_id"] = user.id
    session["auth_version"] = user.auth_version
    session.permanent = True
    logger.info("Login realizado com sucesso.")
    return jsonify({
        "success": True,
        "user": {"id": user.id, "nome": user.nome, "email": user.email, "role": role},
    }), 200


@auth_bp.get('/session')
@validar
def validar_sessao():
    return jsonify({
        "success": True,
        "user": {"id": g.current_user.id, "nome": g.current_user.nome, "email": g.current_user.email, "role": g.current_role},
    }), 200


@auth_bp.post('/logout')
def logout():
    session.clear()
    logger.info("Sessão encerrada.")
    return jsonify({"success": True}), 200


@auth_bp.route('/cadastro', methods=["POST"])
def cadastro():
    data = request.get_json(silent=True)
    if not val.check_json(data):
        logger.warning("Cadastro recusado por conteúdo JSON inválido.")
        return err_json(
                code="INVALID_JSON",
                message="Envie os dados em formato JSON válido",
                status=400
        )
    fields = ['name', 'surname', 'email', 'password','password_confirmation', 'cep', 'country',
    'street', 'number','neighborhood','city', 'state', 'extra']   
    f_info = get_attr(data,fields);
    required = [field for field in fields if field != 'extra']

    missing = [field for field in required if not f_info.get(field)]
    if missing:
        logger.warning("Cadastro recusado por campos obrigatórios ausentes.")
        return err_json(
            code="MISSING_INFO",
            message="Há campos ausentes",
            fields=missing,
            status = 400
        )   
    f_info["email"] = f_info["email"].strip()

    if not val.check_email(f_info['email']):
        logger.warning("Cadastro recusado por formato de e-mail inválido.")
        return err_json(
            code="INVALID_EMAIL",
            message="O email inserido é inválido",
            status = 400
        )        

    if f_info['password'] != f_info['password_confirmation']:
        logger.warning("Cadastro recusado porque as senhas informadas divergem.")
        return err_json(
            code="PASSWORD_DOES_NOT_MATCH",
            message="Senhas inseridas são diferentes",
            status = 409
        )

    infos = [f_info[field] for field in required if field not in ('password','password_confirmation')]
    if not val.check_pwd_strength(f_info['password'],infos):
        logger.warning("Cadastro recusado por senha fraca.")
        return err_json(
            code="WEAK_PASSWORD",
            message="Senha muito fraca, utilize outra senha",
            status = 409
        ) 

    try:
        CRUD.create.cliente_com_endereco(
            nome=f"{f_info['name']} {f_info['surname']}",
            email=f_info['email'],
            senha=f_info['password'],
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
        logger.warning("Cadastro recusado por dados inválidos ou e-mail já registrado.")
        return err_json(
            code="USER_EXISTS",
            message="Email já está registrado.",
            status=409
        )    
    except IntegrityError:
        logger.warning("Conflito de integridade durante o cadastro.")
        return err_json(
            code="INTEGRITY_ERROR",
            message="Não foi possível cadastrar os dados informados",
            status=409
        )
    except SQLAlchemyError:
        logger.exception("Erro no banco durante o cadastro")
        return err_json(
            code="DATABASE_ERROR",
            message="Não foi possível criar a conta",
            status=500
        )
    logger.info("Cadastro criado; confirmação de e-mail será enviada.")
    sendAuthEmail(f_info['email'])
    return jsonify({
        "success": True,
        "message": "Usuário criado com sucesso",
        "user": {"email": f_info['email']}
    }), 201        

@auth_bp.route('/cadastro/validar', methods=["POST"])
def validar_cadastro():
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json(
                code="INVALID_JSON",
                message="Envie os dados em formato JSON válido",
                status=400
        )

    token_input = data.get('token')
    token = token_input.strip() if isinstance(token_input, str) else ""
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
            message="O link de validação é inválido ou expirou. Solicite um novo email",
            status=400
        )

    user = CRUD.read.usuario_por_email(email)
    if not user:
        return err_json(
            code="USER_NOT_FOUND",
            message="Não foi encontrada uma conta para este token",
            status=404
        )

    if not user.email_verificado:
        user.email_verificado = True
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Falha ao confirmar o endereço de e-mail.")
            return err_json("DATABASE_ERROR", "Não foi possível confirmar o e-mail.", status=500)
        logger.info("Endereço de e-mail confirmado.")

    return jsonify({
        "success": True,
        "message": "Email validado com sucesso",
        "user": {"email": user.email}
    }), 200


@auth_bp.post('/password-reset/request')
@limiter.limit("3 per hour")
def request_password_reset():
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    email_input = data.get("email")
    email = email_input.strip() if isinstance(email_input, str) else ""
    if not val.check_email(email):
        logger.warning("Solicitação de redefinição recusada por formato de e-mail inválido.")
        return err_json("VALIDATION_FAILED", "Informe um email válido.", fields={"email": "Email inválido"}, status=400)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    user = CRUD.read.usuario_por_email(email)
    if user is not None:
        token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=current_app.config["PASSWORD_RESET_TOKEN_MINUTES"]),
        )
        db.session.add(token)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Falha ao processar solicitação de redefinição de senha")
        else:
            logger.info("Solicitação de redefinição aceita; envio de e-mail iniciado.")
            Thread(
                target=_send_password_reset_email,
                args=(current_app._get_current_object(), user.email, raw_token),
                daemon=True,
            ).start()
    return jsonify({"success": True, "message": "Se o email estiver cadastrado, enviaremos instruções para redefinir a senha."}), 200


@auth_bp.post('/password-reset/confirm')
@limiter.limit("5 per hour")
def confirm_password_reset():
    data = request.get_json(silent=True)
    if not val.check_json(data):
        return err_json("INVALID_JSON", "Envie os dados em formato JSON válido.", status=400)
    raw_token = data.get("token") if isinstance(data.get("token"), str) else ""
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    confirmation = data.get("password_confirmation") if isinstance(data.get("password_confirmation"), str) else ""
    if not raw_token:
        return err_json("INVALID_OR_EXPIRED_TOKEN", "Token inválido ou expirado.", status=400)
    reset = db.session.execute(db.select(PasswordResetToken).where(
        PasswordResetToken.token_hash == hashlib.sha256(raw_token.encode()).hexdigest()
    )).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if reset is None or reset.used_at is not None or reset.expires_at.replace(tzinfo=timezone.utc) <= now:
        return err_json("INVALID_OR_EXPIRED_TOKEN", "Token inválido ou expirado.", status=400)
    user = db.session.get(Usuario, reset.user_id)
    if user is None:
        return err_json("INVALID_OR_EXPIRED_TOKEN", "Token inválido ou expirado.", status=400)
    if password != confirmation:
        return err_json("PASSWORD_DOES_NOT_MATCH", "As senhas são diferentes.", status=400)
    if not val.check_pwd_strength(password, [user.email, user.nome]):
        return err_json("WEAK_PASSWORD", "Senha muito fraca, utilize outra senha.", status=400)
    try:
        claimed = db.session.execute(db.update(PasswordResetToken).where(
            PasswordResetToken.id == reset.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        ).values(used_at=now).execution_options(synchronize_session=False))
        if claimed.rowcount != 1:
            db.session.rollback()
            return err_json("INVALID_OR_EXPIRED_TOKEN", "Token inválido ou expirado.", status=400)
        user.senha_hash = PasswordHasher().hash(password)
        user.auth_version += 1
        db.session.execute(db.update(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset.id,
            PasswordResetToken.used_at.is_(None),
        ).values(used_at=now))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Falha ao redefinir senha")
        return err_json("DATABASE_ERROR", "Não foi possível redefinir a senha.", status=500)
    session.clear()
    logger.info("Senha redefinida e sessões anteriores invalidadas.")
    return jsonify({"success": True, "message": "Senha redefinida. Entre com a nova senha."}), 200

