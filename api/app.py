#Arquivo para inicialização e reunião do flask
#TODO: Organizar imports dps

import logging
import models
from logging.handlers import RotatingFileHandler
from sqlalchemy.orm import configure_mappers
from pathlib import Path

from flask import Flask
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
    #isso aq é só pra n criar handler duplicado
    if any(handler.name == "sabor-file" for handler in sabor_logger.handlers):
        return
    Path("logs").mkdir(exist_ok=True)
    handler = RotatingFileHandler("logs/logSabor&Clic.log", maxBytes=10485760, backupCount=3)
    handler.set_name("sabor-file")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    sabor_logger.addHandler(handler)
    sabor_logger.setLevel(logging.INFO)

#Vou fazer uma config de teste dps
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    #extensões
    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    Talisman(app, force_https=not app.debug)
    CORS(app, origins=app.config["FRONTEND_BASE_URL"], supports_credentials=True)
    
    #mail
    mail.init_app(app) 
    
    database_path = app.config.get("DATABASE")
    if database_path:
        Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        configure_mappers()
        db.create_all()
        logger.info("Database tables checked")

    #blueprints, serão adicionadas mais posteriormente
    app.register_blueprint(auth_bp)
    app.register_blueprint(bancadas_bp)

    @app.errorhandler(CSRFError)
    def csrf_error_handler(error):
        return err_json("CSRF_VALIDATION_FAILED", "Token CSRF ausente ou inválido.", status=400)

    if not app.testing:
        _configure_logging()

    #Caso tenham muitos erros, criar uma função geral para error handling (para não poluir o código)
    @app.errorhandler(RateLimitExceeded)
    def rate_handler(e):
        logger.warning("Limite de requisições atingido desc:%s",e.description)
        return err_json(
            code="RATE_LIMITED",
            message="Muitas tentativas realizadas, tente novamente após 1 minuto",
            status=429
        ) 

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=app.debug)
