#TODO Depois add redis server pra quando for lançar
#Arquivo relacionado à configuração do ambiente
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

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

    #Trocar isso dps pro redis
    RATELIMIT_STORAGE_URI = os.environ.get(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )