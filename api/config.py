# TODO: Adicionar um servidor Redis antes do lançamento.
# Arquivo relacionado à configuração do ambiente.
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from flask_mail import Mail

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env')
mail = Mail()

# Configuração geral e inicialização do ambiente
class Config:
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    ENVIRONMENT = os.environ.get("APP_ENV", "development").lower()

    # Chaves
    SECRET_KEY = os.environ.get("SECRET_KEY")
    FERNET_KEY = os.environ.get("FERNET_KEY")
    INDEX_KEY = os.environ.get("INDEX_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM = "HS256"
    # Adicionar estas variáveis ao ambiente depois.
    JWT_ACCESS_TOKEN_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_MINUTES", "60"))
    FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL") or (
        "http://localhost:5173" if ENVIRONMENT not in {"production", "prod"} else None
    )
    PASSWORD_RESET_TOKEN_MINUTES = int(os.environ.get("PASSWORD_RESET_TOKEN_MINUTES", "30"))

    # Banco de dados
    DATABASE = Path(
        os.environ.get("DATABASE", str(BASE_DIR / "instances" / "app.db"))
    ).expanduser().resolve() # Normaliza o caminho.
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"hide_parameters": True}

    # Flask-WTF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = 3600

    # Outros
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = bool(int(os.environ.get(
        "SESSION_COOKIE_SECURE", "1" if ENVIRONMENT in {"production", "prod"} else "0"
    )))
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get("JWT_ACCESS_TOKEN_MINUTES", "60")))

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '0') == '1'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', '0') == '1'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or None
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or None
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or None
    MAIL_DEBUG = False

    # Trocar isso pelo Redis depois
    RATELIMIT_STORAGE_URI = os.environ.get(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )
