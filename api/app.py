#Arquivo para inicialização e reunião do flask
#TODO: Organizar imports dps e add flask wtf, flask jwt extended

import db
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask
from flask_talisman import Talisman
from flask_cors import CORS
from flask_limiter.errors import RateLimitExceeded

from utils import err_json
from config import Config
from blueprints.auth import auth_bp
from extensions import limiter

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    #extensões
    db.init_app(app)
    limiter.init_app(app)
    Talisman(app)
    CORS(app)

    #blueprints, serão adicionadas mais posteriormente
    app.register_blueprint(auth_bp)

    #Configuração de log, sujeito a mudança (especificamente a maneira de armazenamento)
    Path("logs").mkdir(exist_ok=True)
    handler = RotatingFileHandler('logs/logTeste.log',maxBytes=10485760,backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO,handlers=[handler])

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
    app.run(host='127.0.0.1', port=5000, debug=True)
