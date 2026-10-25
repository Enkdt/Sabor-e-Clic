import base64
from os import environ as env
from flask import jsonify, render_template_string

#P/ cripto, se precisar mudar dps
from cryptography.fernet import Fernet
from hashlib import blake2b as b2b
from config import Config

#P/ token, se precisar mover dps
from datetime import datetime, timedelta,timezone
import jwt

#P/ Email se precisar depois
from flask_mail import Mail, Message
from config import mail

#code = Código. E.g PAGE NOT FOUND, VALIDATION_FAILED, etc
#msg = Mensagem customizada. E.g "E-mail is required"
#inpField = qual campo pertence. E.g msg anterior pertenceria ao campo de nome email
#status = Código http. E.g 404, 403, 200
def err_json(code, message=None, fields=None, status=400):
    body = {"error":{"code":code}}
    if message:
        body["error"]["message"] = message
    if fields:
        body["error"]["fields"] = fields
    print(body)
    return jsonify(body), status

#Usado para facilitar o unpack do json
def get_attr(origin, keys):
    return {k:(origin.get(k) or ("")).strip() for k in keys}

#Mudar posteriormente para uma pasta services/crypt.py.
fernet_key = Config.FERNET_KEY
index_key = Config.INDEX_KEY
fernet = Fernet(fernet_key)

#Verificar se essa função será reutilizada para o restante dos encrypts
def encrypt(cpf:str) ->  str:
    return fernet.encrypt(cpf.encode()).decode()

def cpf_index(cpf:str):
    #digest é o dado retornado em bytes pós cripto
    digest = b2b(data=cpf.encode(),key=index_key.encode(),digest_size=32).digest()
    #retorna uma string do digest gerado encryptado por b64
    return base64.urlsafe_b64encode(digest).decode()

def decrypt(enc_cpf:str) ->  str:
    return fernet.decrypt(enc_cpf.encode()).decode()

#Mudar posteriormenteee pra uma pasta services/token.py

secretKey = Config.SECRET_KEY
def generateToken(email:str, purpose:str, expirationMinutes:int = 15):

    expirationTime = datetime.now(timezone.utc) + timedelta(minutes=expirationMinutes)
    payload = {"email":email, "exp":expirationTime,"iat":datetime.now(timezone.utc),"purpose":purpose}
    return jwt.encode(payload,secretKey,algorithm="HS256")

def validateToken(token:str,purpose:str):
    try:
        payload = jwt.decode(token,secretKey,algorithms=["HS256"])
        if payload["purpose"] != purpose:
            return None
        return payload["email"]
    except Exception:
        #Engloba jwt.ExpiredSignatureError e InvalidToken
        return None

#Mudar posteriormente para sevicees/email.py

def sendEmail(Subject:str,recipient:str,content:str,HTMLcontent:str):
    #Ver se recipieent vai tar criptografado
    message = Message(subject=Subject, recipients=[recipient])
    message.body = content
    message.html = HTMLcontent
    mail.send(message)

def sendAuthEmail(recipient:str, token:str):
    #Trocar a url depois em produção
    verificationLink = f"http://localhost:5173/cadastro/autenticar?{token}"
    subject = "Valide a criação da conta no serviço Sabor&Clic"
    content = f'Valide seu email clicando neste link: {verificationLink}'
    htmlContent = render_template_string('''
        <p>Clique no botão abaixo para realizar a validação da conta no serviço :)</p>
        <p><a href="{{link}}">Validar Email</a></p>
        <p>Caso não funcione, copie e cole esta url em seu navegador</p>
        <p>{{link}}</p>
    ''', link=verificationLink)

    sendEmail(subject,recipient,content,htmlContent)

