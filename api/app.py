# Arquivo de inicialização e configuração do Flask.
# TODO: Organizar as importações depois.

import logging
from time import perf_counter
import models
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm import configure_mappers
from pathlib import Path
from urllib.parse import urlsplit
from sqlalchemy import inspect, text

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
from extensions import csrf, db, limiter

logger = logging.getLogger(__name__)

def _configure_logging():
    sabor_logger = logging.getLogger()
    # Isso evita a criação de manipuladores duplicados.
    if any(handler.name == "sabor-file" for handler in sabor_logger.handlers):
        return
    Path("logs").mkdir(exist_ok=True)
    handler = RotatingFileHandler("logs/logSabor&Clic.log", maxBytes=10485760, backupCount=3)
    handler.set_name("sabor-file")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    sabor_logger.addHandler(handler)
    sabor_logger.setLevel(logging.INFO)

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

    try:
        with app.app_context():
            configure_mappers()
            db.create_all()
            if "preco_hora" not in {column["name"] for column in inspect(db.engine).get_columns("bancada")}:
                db.session.execute(text(
                    "ALTER TABLE bancada ADD COLUMN preco_hora NUMERIC(10, 2) NOT NULL DEFAULT 40.00"
                ))
                db.session.commit()
            if db.engine.dialect.name == "sqlite":
                db.session.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS prevent_agendamento_overlap_insert
                    BEFORE INSERT ON agendamento
                    WHEN EXISTS (
                        SELECT 1 FROM agendamento existing
                        WHERE existing.id_bancada = NEW.id_bancada
                          AND julianday(NEW.horario_agendado) < julianday(existing.horario_agendado) + (existing.tempo_agendado / 1440.0)
                          AND julianday(existing.horario_agendado) < julianday(NEW.horario_agendado) + (NEW.tempo_agendado / 1440.0)
                    )
                    BEGIN
                        SELECT RAISE(ABORT, 'A bancada já tem um agendamento nesse intervalo.');
                    END
                """))
                db.session.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS prevent_agendamento_overlap_update
                    BEFORE UPDATE OF id_bancada, horario_agendado, tempo_agendado ON agendamento
                    WHEN EXISTS (
                        SELECT 1 FROM agendamento existing
                        WHERE existing.id != NEW.id
                          AND existing.id_bancada = NEW.id_bancada
                          AND julianday(NEW.horario_agendado) < julianday(existing.horario_agendado) + (existing.tempo_agendado / 1440.0)
                          AND julianday(existing.horario_agendado) < julianday(NEW.horario_agendado) + (NEW.tempo_agendado / 1440.0)
                    )
                    BEGIN
                        SELECT RAISE(ABORT, 'A bancada já tem um agendamento nesse intervalo.');
                    END
                """))
                db.session.commit()
            if "auth_version" not in {column["name"] for column in inspect(db.engine).get_columns("usuario")}:
                db.session.execute(text("ALTER TABLE usuario ADD COLUMN auth_version INTEGER NOT NULL DEFAULT 1"))
                db.session.commit()
                logger.info("Migração da coluna de versão de autenticação concluída.")
            logger.info("Estrutura do banco de dados verificada.")
    except Exception:
        logger.exception("Falha ao inicializar o banco de dados.")
        raise

    # Blueprints; outras serão adicionadas depois.
    app.register_blueprint(auth_bp)
    app.register_blueprint(bancadas_bp)

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
