import logging
import re
import unicodedata

from threading import Thread
from flask import current_app, jsonify, render_template_string

# Para tokens. Mover depois, se necessário.
from datetime import datetime, timedelta,timezone
import jwt

# Para email. Mover depois, se necessário.
from flask_mail import Message
from config import mail

logger = logging.getLogger(__name__)

# code = código, por exemplo PAGE_NOT_FOUND ou VALIDATION_FAILED
# msg = mensagem personalizada, por exemplo "O e-mail é obrigatório"
# inpField = campo ao qual a mensagem pertence, por exemplo "email"
# status = código HTTP, por exemplo 404, 403 ou 200
def err_json(code, message=None, fields=None, status=400):
    """Gera um erro em formato json que é retornado ao front-end"""
    body = {"error":{"code":code}}
    if message:
        body["error"]["message"] = message
    if fields:
        body["error"]["fields"] = fields
    logger.debug("Erro da api: %s", code)
    return jsonify(body), status

# Usado para facilitar a leitura dos dados JSON
def get_attr(origin, keys):
    """Função para desempacotar o json recebido do front end, armazenando-o em um dicionário"""
    return {key: value.strip() if isinstance(value := origin.get(key), str) else "" for key in keys}

# Mover depois para services/token.py

def generateToken(email:str, purpose:str, expirationMinutes:int = 15):
    """Gera o token do usuário a partir de seus dados, com propósito e tempo de expiração"""
    expirationTime = datetime.now(timezone.utc) + timedelta(minutes=expirationMinutes)
    payload = {"email":email, "exp":expirationTime,"iat":datetime.now(timezone.utc),"purpose":purpose}
    return jwt.encode(payload,current_app.config["JWT_SECRET_KEY"],algorithm=current_app.config["JWT_ALGORITHM"])

def validateToken(token:str,purpose:str):
    """Valida o token de sessão do usuário, propósito fornecido pelo token e pela validação devem ser o mesmo para que haja a validação"""
    
    try:
        payload = jwt.decode(token,current_app.config["JWT_SECRET_KEY"],algorithms=[current_app.config["JWT_ALGORITHM"]])
        email = payload.get("email")
        if payload.get("purpose") != purpose or not isinstance(email, str) or not email:
            return None
        return email
    except (jwt.PyJWTError, TypeError):
        return None

# Mover depois para services/email.py

def sendEmail(Subject:str,recipient:str,content:str,HTMLcontent:str):
    """Função genérica de envio de email a determinado usuário"""

    message = Message(subject=Subject, recipients=[recipient])
    message.body = content
    message.html = HTMLcontent
    mail.send(message)


def sendEmailAsync(app, Subject, recipient, content, HTMLcontent):
    # Envia o email fora do ciclo requisição/resposta; falha de SMTP é registrada sem parar o serviço
    with app.app_context():
        try:
            sendEmail(Subject, recipient, content, HTMLcontent)
        except Exception:
            logger.exception("Falha ao enviar email para %s.", recipient)


def sendAuthEmail(recipient:str):
    """Dispara, em segundo plano, o email de autenticação da conta ao usuário.

    O link/token é gerado na requisição (precisa de current_app); o envio SMTP
    roda em uma thread para que lentidão ou falha do servidor de email nunca
    quebre o cadastro (o usuário pode revalidar o email depois).
    """

    token = generateToken(recipient,"user validation",15)
    verificationLink = (
        f"{current_app.config['FRONTEND_BASE_URL'].rstrip('/')}/cadastro/autenticar?token={token}"
    )
    subject = "Valide a criação da conta no serviço Sabor&Clic"
    content = f'Valide seu email clicando neste link: {verificationLink}'
    htmlContent = render_template_string('''
        <p>Clique no botão abaixo para realizar a validação da conta no serviço :)</p>
        <p><a href="{{link}}">Validar Email</a></p>
        <p>Caso não funcione, copie e cole esta url em seu navegador</p>
        <p>{{link}}</p>
    ''', link=verificationLink)

    Thread(
        target=sendEmailAsync,
        args=(current_app._get_current_object(), subject, recipient, content, htmlContent),
        daemon=True,
    ).start()




def slugify(texto: str) -> str:
    """Gera um slug ASCII a partir de um nome (ex.: 'Cantina São José' -> 'cantina-sao-jose')."""
    normalizado = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    normalizado = re.sub(r"[^a-zA-Z0-9]+", "-", normalizado).strip("-").lower()
    return normalizado or "restaurante"
