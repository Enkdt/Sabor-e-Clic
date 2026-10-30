import logging
from flask import current_app, jsonify, render_template_string

#P/ token, se precisar mover dps
from datetime import datetime, timedelta,timezone
import jwt

#P/ Email se precisar depois
from flask_mail import Message
from config import mail

logger = logging.getLogger(__name__)

#code = Código. E.g PAGE NOT FOUND, VALIDATION_FAILED, etc
#msg = Mensagem customizada. E.g "E-mail is required"
#inpField = qual campo pertence. E.g msg anterior pertenceria ao campo de nome email
#status = Código http. E.g 404, 403, 200
def err_json(code, message=None, fields=None, status=400):
    """Gera um erro em formato json que é retornado ao front-end"""
    body = {"error":{"code":code}}
    if message:
        body["error"]["message"] = message
    if fields:
        body["error"]["fields"] = fields
    logger.debug("Erro da api: %s", code)
    return jsonify(body), status

#Usado para facilitar o unpack do json
def get_attr(origin, keys):
    """Função para desempacotar o json recebido do front end, armazenando-o em um dicionário"""
    return {key: value.strip() if isinstance(value := origin.get(key), str) else "" for key in keys}

#Mudar posteriormenteee pra uma pasta services/token.py

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

#Mudar posteriormente para sevicees/email.py

def sendEmail(Subject:str,recipient:str,content:str,HTMLcontent:str):
    """Função genérica de envio de email a determinado usuário"""

    message = Message(subject=Subject, recipients=[recipient])
    message.body = content
    message.html = HTMLcontent
    mail.send(message)

def sendAuthEmail(recipient:str):
    """Função de envio de email de autenticação ao usuário"""

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

    sendEmail(subject,recipient,content,htmlContent)

