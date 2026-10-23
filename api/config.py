#TODO Depois add redis server pra quando for lançar
#Arquivo relacionado à configuração do ambiente
import os
from pathlib import Path
from dotenv import load_dotenv
from flask_mail import Mail

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env')
mail = Mail()

#Configuração geral e setup do ambiente
class Config:
    #KEYS
    SECRET_KEY = os.environ.get("SECRET_KEY")
    FERNET_KEY = os.environ.get("FERNET_KEY")
    INDEX_KEY = os.environ.get("INDEX_KEY")

    # DATABASE
    DATABASE = Path(
        os.environ.get("DATABASE", str(BASE_DIR / "instances" / "app.db"))
    ).expanduser().resolve() # Normaliza o caminho

    DATABASE.parent.mkdir(parents=True, exist_ok=True) # Cria certinho a pasta caso ela não exista

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #OTHERS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    #MAIL

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT'))
    MAIL_USE_TLS = bool(int(os.environ.get('MAIL_USE_TLS')))
    MAIL_USE_SSL = bool(int(os.environ.get('MAIL_USE_SSL')))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    #Trocar isso dps pro redis
    RATELIMIT_STORAGE_URI = os.environ.get(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )