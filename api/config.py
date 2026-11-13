# Arquivo relacionado à configuração do ambiente.
#
# Regras de ambiente (SEC-001 / PROD-003):
#   - APP_ENV deve ser exatamente "development", "test" ou "production".
#     Um valor desconhecido falha fechado (RuntimeError) em vez de assumir
#     silenciosamente "development".
#   - Em produção, segredos e URLs são obrigatórios e validados; NÃO existe
#     mais chave secreta embutida como fallback (ver app.py).
#   - A URI do banco é resolvida por ambiente: produção/teste exigem uma URL
#     explícita; desenvolvimento pode cair para um SQLite local documentado.
import os
import secrets
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from flask_mail import Mail

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env')
mail = Mail()

_VALID_ENVIRONMENTS = {"development", "test", "production"}


def _resolve_environment() -> str:
    """Resolve e valida APP_ENV. Falha fechado para valores desconhecidos."""
    raw = os.environ.get("APP_ENV")
    if raw is None or raw == "":
        # Sem APP_ENV explícito assumimos desenvolvimento local. Em produção o
        # deploy DEVE definir APP_ENV=production; app.py recusa iniciar sem os
        # segredos exigidos, então não há caminho fail-open com chave embutida.
        return "development"
    env = raw.strip().lower()
    if env in {"prod"}:
        env = "production"
    if env in {"dev"}:
        env = "development"
    if env not in _VALID_ENVIRONMENTS:
        raise RuntimeError(
            "APP_ENV inválido. Use 'development', 'test' ou 'production'."
        )
    return env


def _resolve_database_uri(environment: str):
    """URI do banco por ambiente.

    - production: exige DATABASE_URL explícita (ex.: Postgres/Neon).
    - test: usa DATABASE_URL se fornecida, senão SQLite em memória.
    - development: usa DATABASE_URL se fornecida, senão SQLite local em
      instances/app.db (documentado no .env.example).
    """
    explicit = os.environ.get("DATABASE_URL")
    if explicit:
        return explicit
    if environment == "production":
        # Sem fallback silencioso: produção precisa de um banco gerenciado.
        return None
    if environment == "test":
        return "sqlite:///:memory:"
    local_path = Path(
        os.environ.get("DATABASE", str(BASE_DIR / "instances" / "app.db"))
    ).expanduser().resolve()
    return f"sqlite:///{local_path}"


# Configuração geral e inicialização do ambiente
class Config:
    ENVIRONMENT = _resolve_environment()
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1" and ENVIRONMENT != "production"

    # Chaves.
    # Em desenvolvimento/teste, se SECRET_KEY não for fornecida, geramos uma
    # chave efêmera por processo (nunca uma constante previsível). Em produção
    # app.py recusa iniciar quando SECRET_KEY está ausente ou fraca.
    SECRET_KEY = os.environ.get("SECRET_KEY") or (
        secrets.token_urlsafe(48) if ENVIRONMENT != "production" else None
    )
    FERNET_KEY = os.environ.get("FERNET_KEY")
    INDEX_KEY = os.environ.get("INDEX_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_MINUTES", "60"))
    FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL") or (
        "http://localhost:5173" if ENVIRONMENT != "production" else None
    )
    PASSWORD_RESET_TOKEN_MINUTES = int(os.environ.get("PASSWORD_RESET_TOKEN_MINUTES", "30"))

    # Banco de dados.
    # DATABASE mantém apenas o caminho local do SQLite (dev); a URI efetiva é
    # resolvida por ambiente em _resolve_database_uri.
    DATABASE = Path(
        os.environ.get("DATABASE", str(BASE_DIR / "instances" / "app.db"))
    ).expanduser().resolve()
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri(ENVIRONMENT)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"hide_parameters": True}

    # Flask-WTF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = 3600

    # Limite global do corpo da requisição (API-002): barra uploads/multipart gigantes
    # antes de chegarem aos handlers. 4 MB cobre a imagem de 2 MB + overhead do multipart.
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", str(4 * 1024 * 1024)))

    # Cookies de sessão. Seguro por padrão em produção.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = bool(int(os.environ.get(
        "SESSION_COOKIE_SECURE", "1" if ENVIRONMENT == "production" else "0"
    )))
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_MINUTES", "60"))
    )

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '0') == '1'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', '0') == '1'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or None
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or None
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or None
    MAIL_DEBUG = False

    # Rate limit: memória em dev; produção deve apontar para um store compartilhado
    # (ver SEC-003). Nunca usar este store como armazenamento de logs.
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    # Habilitado por padrão. Desligado apenas em contextos de teste/E2E (muitos
    # logins em sequência) via RATELIMIT_ENABLED=0. Lido no init do Flask-Limiter.
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "1") != "0"

    # Logs no Redis (Upstash REST). Opcional: quando ambos estão presentes, os
    # logs continuam indo para stdout E são empurrados (best-effort) para uma
    # lista no Redis via API REST. Ausentes => apenas stdout. Nunca usado como
    # caminho crítico: falha silenciosa e timeout curto.
    UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or None
    UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or None
    # Chave (lista) onde os logs são acumulados e tamanho máximo retido.
    LOG_REDIS_KEY = os.environ.get("LOG_REDIS_KEY", "logs:app")
    LOG_REDIS_MAX_ENTRIES = int(os.environ.get("LOG_REDIS_MAX_ENTRIES", "5000"))
    # Timeout (segundos) da chamada REST. Curto de propósito: nunca atrasar a resposta.
    LOG_REDIS_TIMEOUT = float(os.environ.get("LOG_REDIS_TIMEOUT", "1.5"))
