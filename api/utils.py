import base64
from os import environ as env
from flask import jsonify
from cryptography.fernet import Fernet
from hashlib import blake2b as b2b
from config import Config

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
def get_attr(origin,keys):
    return {k:(data.get(k) or ("")).strip() for k in keys}

#Mudar posteriormente para uma pasta services, arquivo crypt.py.
fernet_key = Config.FERNET_KEY
index_key = Config.INDEX_KEY
fernet = Fernet(fernet_key)

#Verificar se essa função será reutilizada para o restante dos encrypts
def encrypt_cpf(cpf:str) ->  str:
    return fernet.encrypt(cpf.encode()).decode()

def cpf_index(cpf:str):
    #digest é o dado retornado em bytes pós cripto
    digest = b2b(data=cpf.encode(),key=index_key.encode(),digest_size=32).digest()
    #retorna uma string do digest gerado encryptado por b64
    return base64.urlsafe_b64encode(digest).decode()

def decrypt_cpf(enc_cpf:string) ->  str:
    return fernet.decrypt(enc_cpf.encode()).decode()
