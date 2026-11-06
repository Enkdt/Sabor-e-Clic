# Arquivo de inicialização e configuração do Flask.
# TODO: Organizar as importações depois.

import logging
import os
from time import perf_counter
import models
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, g, request
from werkzeug.exceptions import HTTPException
from flask_talisman import Talisman
from flask_cors import CORS
from flask_limiter.errors import RateLimitExceeded
from flask_wtf.csrf import CSRFError

from utils import err_json
from config import Config, mail
from blueprints.auth import auth_bp
from blueprints.bancadas import bancadas_bp
from blueprints.cardapio import cardapio_bp
from blueprints.clientes import clientes_bp
from blueprints.cozinha import cozinha_bp
from blueprints.dashboard import dashboard_bp
from blueprints.estoque import estoque_bp
from blueprints.pedidos import pedidos_bp
from blueprints.usuarios import usuarios_bp
from blueprints.uploads import uploads_bp
from extensions import csrf, db, limiter
from migrations import run_migrations

logger = logging.getLogger(__name__)

# Diretório do log fixado em api/logs, não no diretório de trabalho do processo.
LOG_DIR = Path(__file__).resolve().parent / "logs"

def _configure_logging():
    # Sob o reloader do Werkzeug a aplicação é importada em dois processos (monitor + worker);
    # se ambos abrirem o RotatingFileHandler no mesmo arquivo, o rollover corrompe o log.
    # Só o processo que realmente atende requisições escreve no arquivo.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "false":
        return
    root_logger = logging.getLogger()
    # Isso evita a criação de manipuladores duplicados.
    if any(getattr(handler, "name", None) == "sabor-file" for handler in root_logger.handlers):
        return
    LOG_DIR.mkdir(exist_ok=True)
    handler = RotatingFileHandler(LOG_DIR / "logSabor&Clic.log", maxBytes=10485760, backupCount=3)
    handler.set_name("sabor-file")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

# Criar uma configuração de teste depois.
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.testing:
        _configure_logging()
    if app.config.get("ENVIRONMENT") in {"production", "prod"}:
        secret_key = app.config.get("SECRET_KEY")
        if not isinstance(secret_key, str) or len(secret_key) < 32:
            logger.error("Inicialização recusada: chave secreta de produção ausente ou fraca.")
            raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres em produção.")
        frontend_origin = app.config.get("FRONTEND_BASE_URL")
        parsed_origin = urlsplit(frontend_origin or "")
        if parsed_origin.scheme != "https" or not parsed_origin.hostname or parsed_origin.path not in {"", "/"} or parsed_origin.username or parsed_origin.password or parsed_origin.query or parsed_origin.fragment:
            logger.error("Inicialização recusada: origem HTTPS do frontend inválida.")
            raise RuntimeError("FRONTEND_BASE_URL deve conter uma origem HTTPS confiável em produção.")
        if not app.config.get("SESSION_COOKIE_SECURE") or not app.config.get("SESSION_COOKIE_HTTPONLY") or app.config.get("SESSION_COOKIE_SAMESITE") not in {"Lax", "Strict"}:
            logger.error("Inicialização recusada: configuração insegura de cookies de sessão.")
            raise RuntimeError("Cookies de sessão precisam manter Secure, HttpOnly e SameSite em produção.")
        if app.config.get("DEBUG"):
            logger.error("Inicialização recusada: modo de depuração ativo em produção.")
            raise RuntimeError("DEBUG não pode estar ativo em produção.")
    # Remover depois.
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = "desenvolvimento-local-inseguro"

    logger.info("Iniciando a aplicação no ambiente %s.", app.config.get("ENVIRONMENT", "desconhecido"))

    # Extensões.
    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    Talisman(
        app,
        force_https=app.config.get("ENVIRONMENT") in {"production", "prod"} or (not app.debug and not app.testing),
        content_security_policy={
            "default-src": "'self'",
            "object-src": "'none'",
            "script-src": "'self' https://vlibras.gov.br",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com https://vlibras.gov.br https://*.vlibras.gov.br",
            "font-src": "'self' https://fonts.gstatic.com https://*.gstatic.com",
            "img-src": "'self' data: https://vlibras.gov.br https://*.vlibras.gov.br",
            "frame-src": "'self' https://vlibras.gov.br https://*.vlibras.gov.br",
            "connect-src": "'self' https://fonts.googleapis.com https://fonts.gstatic.com https://vlibras.gov.br https://*.vlibras.gov.br",
        },
    )
    CORS(app, origins=app.config["FRONTEND_BASE_URL"], supports_credentials=True)
    
    # E-mail.
    mail.init_app(app) 
    
    database_path = app.config.get("DATABASE")
    if database_path:
        Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    run_migrations(app)

    # Blueprints; outras serão adicionadas depois.
    app.register_blueprint(auth_bp)
    app.register_blueprint(bancadas_bp)
    app.register_blueprint(cardapio_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(cozinha_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(uploads_bp)

    @app.errorhandler(CSRFError)
    def csrf_error_handler(error):
        logger.warning("Requisição rejeitada por falha de CSRF na rota %s.", request.path)
        return err_json("CSRF_VALIDATION_FAILED", "Token CSRF ausente ou inválido.", status=400)

    @app.before_request
    def start_request_log():
        g.request_started_at = perf_counter()

    @app.after_request
    def log_request(response):
        elapsed_ms = (perf_counter() - getattr(g, "request_started_at", perf_counter())) * 1000
        logger.info("HTTP %s %s respondeu %s em %.1f ms.", request.method, request.path, response.status_code, elapsed_ms)
        return response

    @app.errorhandler(Exception)
    def unhandled_error(error):
        if isinstance(error, HTTPException):
            return error
        logger.exception("Erro não tratado durante a requisição %s %s.", request.method, request.path)
        return err_json("INTERNAL_SERVER_ERROR", "Ocorreu um erro interno.", status=500)

    # Se houver muitos erros, criar uma função geral para tratá-los e evitar poluir o código.
    @app.errorhandler(RateLimitExceeded)
    def rate_handler(e):
        logger.warning("Limite de requisições atingido na rota %s.", request.path)
        return err_json(
            code="RATE_LIMITED",
            message="Muitas tentativas realizadas, tente novamente após 1 minuto",
            status=429
        ) 

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=app.debug)
