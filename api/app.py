# Arquivo de inicialização e configuração do Flask.

import logging
import json
import os
import re
import sys
import uuid
from time import perf_counter, time
from urllib import error as _urllib_error
from urllib import request as _urllib_request
from urllib.parse import urlsplit

# Garante que o diretório desta aplicação (api/) esteja em sys.path antes de
# importar módulos irmãos (models, config, blueprints, utils, extensions).
# Necessário porque o runtime Python da Vercel carrega este arquivo via
# importlib.util.spec_from_file_location, que NÃO adiciona o diretório do
# entrypoint ao sys.path. Sem isto, "import models" falha com
# ModuleNotFoundError e a função serverless retorna 500 no boot. Rodar
# localmente com CWD=api/ mascara o problema. Idempotente e seguro em todos
# os ambientes.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import models  # noqa: E402, F401  (registra os modelos no metadata do SQLAlchemy)
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

logger = logging.getLogger(__name__)

# Campos que nunca devem aparecer em logs (PROD-001).
_SENSITIVE_HINTS = ("password", "senha", "token", "secret", "cookie", "authorization", "database_url")

# Captura "scheme://user:pass@host..." (apenas com credenciais embutidas) para
# redigir strings de conexão sem mexer em URLs públicas normais.
_CONN_STRING_RE = re.compile(r"(\b[a-zA-Z][a-zA-Z0-9+.-]*)://[^\s/'\"]+:[^\s/'\"]+@[^\s'\"]+")


def _redact(message: str) -> str:
    """Redação best-effort de connection strings com credenciais embutidas."""
    return _CONN_STRING_RE.sub(r"\1://[redacted]", message)


class _RedactingFormatter(logging.Formatter):
    """Formatter de linha única para stdout.

    Serverless (Vercel) captura stdout/stderr; não há arquivo durável. Este
    formatter também faz uma redação best-effort de valores sensíveis que
    tenham escorrido para a mensagem.
    """

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        # Redação best-effort de connection strings (ex.: postgresql://user:pass@host).
        return _redact(message)


class UpstashLogHandler(logging.Handler):
    """Envia cada log para uma lista no Redis via Upstash REST (OBS-001).

    Desenho intencional para serverless:
      - Best-effort: nunca propaga exceções (usa handleError). Se o Redis
        estiver fora ou lento, a requisição não é afetada.
      - Sem workers de longa duração: a escrita é uma única chamada HTTP
        síncrona com timeout curto. O stdout continua sendo o log primário.
      - LPUSH + LTRIM em pipeline, para a lista não crescer sem limite.
      - Reaproveita a redação de segredos do formatter.

    Não armazena o token no log; só o usa no cabeçalho Authorization.
    """

    def __init__(self, base_url: str, token: str, *, key: str,
                 max_entries: int, timeout: float):
        super().__init__()
        # Normaliza para evitar barra dupla ao montar o endpoint do pipeline.
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._key = key
        self._max_entries = max_entries
        self._timeout = timeout
        # Evita inundar o stderr quando o Redis está mal configurado/indisponível:
        # só avisa uma vez por janela. Ajuda a DIAGNOSTICAR por que "nada chega".
        self._last_warn_at = 0.0

    def _warn_once(self, detail: str) -> None:
        """Avisa no stderr (fora do logging, para não recorrer ao próprio handler)
        no máximo uma vez a cada 60s. Torna uma falha silenciosa observável."""
        now = time()
        if now - self._last_warn_at < 60:
            return
        self._last_warn_at = now
        try:
            print(f"[UpstashLogHandler] falha ao enviar log ao Redis: {detail}",
                  file=sys.stderr, flush=True)
        except Exception:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = json.dumps({
                "ts": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": _redact(self.format(record)),
            }, ensure_ascii=False)
            # Pipeline REST: LPUSH <key> <payload> ; LTRIM <key> 0 max-1.
            commands = [
                ["LPUSH", self._key, payload],
                ["LTRIM", self._key, "0", str(self._max_entries - 1)],
            ]
            body = json.dumps(commands).encode("utf-8")
            req = _urllib_request.Request(
                f"{self._base_url}/pipeline",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
            )
            # Timeout curto: nunca segurar a resposta por causa de telemetria.
            with _urllib_request.urlopen(req, timeout=self._timeout) as resp:
                # Valida a resposta: o Upstash responde 200 com um array JSON, mas
                # pode conter {"error": ...} por comando SEM status HTTP de erro.
                # Sem checar isso, uma config errada (token/URL) falharia em silêncio
                # e "nenhum log chegaria" sem qualquer pista — a causa deste bug.
                raw = resp.read().decode("utf-8", "replace")
                self._check_pipeline_response(resp.status, raw)
        except _urllib_error.HTTPError as http_err:
            # 401 (token inválido), 400 (sintaxe), etc. Agora é visível no stderr.
            detail = f"HTTP {http_err.code}"
            try:
                detail += f" {http_err.read().decode('utf-8', 'replace')[:200]}"
            except Exception:
                pass
            self._warn_once(detail)
            self.handleError(record)
        except Exception as err:
            # Best-effort: falha de telemetria nunca derruba o request, mas avisa.
            self._warn_once(repr(err))
            self.handleError(record)

    def _check_pipeline_response(self, status: int, raw: str) -> None:
        """Levanta se a resposta do pipeline indicar falha (status != 200 ou
        qualquer item com 'error'). Chamado dentro do try de emit."""
        if status != 200:
            raise RuntimeError(f"status inesperado {status}: {raw[:200]}")
        try:
            parsed = json.loads(raw)
        except ValueError:
            raise RuntimeError(f"resposta não-JSON: {raw[:200]}")
        itens = parsed if isinstance(parsed, list) else [parsed]
        for item in itens:
            if isinstance(item, dict) and item.get("error"):
                raise RuntimeError(f"erro do Redis: {item['error']}")


def _configure_logging(app: Flask) -> None:
    """Configura um único StreamHandler para stdout (PROD-001).

    Idempotente entre múltiplas invocações do factory (evita handlers
    duplicados em cold starts/ reloads). Nunca escreve em disco.
    """
    root_logger = logging.getLogger()
    if any(getattr(h, "name", None) == "sabor-stream" for h in root_logger.handlers):
        # Stream já configurado; ainda assim garante o handler de Redis (idempotente).
        _configure_redis_logging(app, root_logger)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.set_name("sabor-stream")
    handler.setFormatter(_RedactingFormatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    root_logger.addHandler(handler)
    level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    root_logger.setLevel(level)

    _configure_redis_logging(app, root_logger)


def _configure_redis_logging(app: Flask, root_logger: logging.Logger) -> None:
    """Anexa um UpstashLogHandler quando as credenciais REST estão presentes.

    Fail-safe: sem URL/token, mantém apenas stdout. Idempotente (não duplica
    handlers em cold starts). O stdout permanece como log primário.
    """
    base_url = app.config.get("UPSTASH_REDIS_REST_URL")
    token = app.config.get("UPSTASH_REDIS_REST_TOKEN")
    if not base_url or not token:
        return
    if any(getattr(h, "name", None) == "sabor-redis" for h in root_logger.handlers):
        return
    redis_handler = UpstashLogHandler(
        base_url,
        token,
        key=app.config.get("LOG_REDIS_KEY", "logs:app"),
        max_entries=app.config.get("LOG_REDIS_MAX_ENTRIES", 5000),
        timeout=app.config.get("LOG_REDIS_TIMEOUT", 1.5),
    )
    redis_handler.set_name("sabor-redis")
    redis_handler.setFormatter(_RedactingFormatter("%(message)s"))
    # Loga a ativação ANTES de anexar, para não forçar esta linha pelo próprio
    # handler recém-criado (evita uma chamada de rede imediata no boot).
    logger.info("Logs também serão enviados ao Redis (Upstash REST).")
    root_logger.addHandler(redis_handler)


def _validate_production_config(app: Flask) -> None:
    """Falha fechado se a configuração de produção estiver insegura (SEC-001)."""
    secret_key = app.config.get("SECRET_KEY")
    if not isinstance(secret_key, str) or len(secret_key) < 32:
        logger.error("Inicialização recusada: SECRET_KEY de produção ausente ou fraca.")
        raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres em produção.")

    jwt_key = app.config.get("JWT_SECRET_KEY")
    if not isinstance(jwt_key, str) or len(jwt_key) < 32:
        logger.error("Inicialização recusada: JWT_SECRET_KEY de produção ausente ou fraca.")
        raise RuntimeError("JWT_SECRET_KEY deve ter pelo menos 32 caracteres em produção.")

    frontend_origin = app.config.get("FRONTEND_BASE_URL")
    parsed = urlsplit(frontend_origin or "")
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.path not in {"", "/"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        logger.error("Inicialização recusada: origem HTTPS do frontend inválida.")
        raise RuntimeError("FRONTEND_BASE_URL deve conter uma origem HTTPS confiável em produção.")

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not isinstance(db_uri, str) or not db_uri.strip():
        logger.error("Inicialização recusada: DATABASE_URL ausente em produção.")
        raise RuntimeError("DATABASE_URL é obrigatório em produção.")
    if db_uri.startswith("sqlite"):
        logger.error("Inicialização recusada: SQLite não é permitido em produção.")
        raise RuntimeError("Produção exige um banco gerenciado (não SQLite).")

    if (
        not app.config.get("SESSION_COOKIE_SECURE")
        or not app.config.get("SESSION_COOKIE_HTTPONLY")
        or app.config.get("SESSION_COOKIE_SAMESITE") not in {"Lax", "Strict"}
    ):
        logger.error("Inicialização recusada: configuração insegura de cookies de sessão.")
        raise RuntimeError("Cookies de sessão precisam manter Secure, HttpOnly e SameSite em produção.")

    if app.config.get("DEBUG"):
        logger.error("Inicialização recusada: modo de depuração ativo em produção.")
        raise RuntimeError("DEBUG não pode estar ativo em produção.")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    is_production = app.config.get("ENVIRONMENT") == "production"

    if is_production:
        _validate_production_config(app)
    elif not app.config.get("SECRET_KEY"):
        # Dev/teste sem SECRET_KEY: chave efêmera por processo (nunca constante
        # previsível). Produção já falhou acima se faltasse chave.
        import secrets as _secrets
        app.config["SECRET_KEY"] = _secrets.token_urlsafe(48)

    if not app.testing:
        _configure_logging(app)

    logger.info("Iniciando a aplicação no ambiente %s.", app.config.get("ENVIRONMENT", "desconhecido"))

    # Extensões.
    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    Talisman(
        app,
        force_https=is_production or (not app.debug and not app.testing),
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

    # STOR-001: em produção, falha cedo se o backend de imagens não estiver configurado.
    if is_production:
        import storage as _storage
        _storage.ensure_configured()

    # Diretório do SQLite local (apenas dev/teste com caminho de arquivo).
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI") or ""
    if db_uri.startswith("sqlite:///") and ":memory:" not in db_uri:
        from pathlib import Path
        sqlite_path = db_uri.replace("sqlite:///", "", 1)
        if sqlite_path:
            Path(sqlite_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    # NOTA (TEST-001/PROD-002): migrações NÃO rodam mais na criação do app em
    # produção/dev. Apps de teste (TESTING=True + SQLite em arquivo) recebem o
    # esquema via migração baseline para paridade com produção (inclui triggers).
    if app.testing and db_uri.startswith("sqlite") and ":memory:" not in db_uri:
        from migrations import init_test_schema
        init_test_schema(app)

    # Blueprints.
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

    @app.get("/api/health")
    def health():
        # OBS-001: liveness — não toca no banco; apenas confirma que o processo responde.
        return {"status": "ok"}, 200

    @app.get("/api/ready")
    def ready():
        # OBS-001: readiness — verifica conectividade com o banco. Não vaza config.
        from sqlalchemy import text
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ready"}, 200
        except Exception:
            logger.exception("Readiness falhou: banco indisponível.")
            return {"status": "unavailable"}, 503

    @app.errorhandler(CSRFError)
    def csrf_error_handler(error):
        logger.warning("Requisição rejeitada por falha de CSRF na rota %s.", request.path)
        return err_json("CSRF_VALIDATION_FAILED", "Token CSRF ausente ou inválido.", status=400)

    @app.before_request
    def start_request_log():
        g.request_started_at = perf_counter()
        # OBS-001: ID de correlação por requisição. Reusa o do cliente/proxy quando
        # presente; senão gera um. Fica disponível em g e no cabeçalho de resposta.
        incoming = request.headers.get("X-Request-ID")
        g.request_id = incoming if incoming and len(incoming) <= 64 else uuid.uuid4().hex

    @app.after_request
    def log_request(response):
        elapsed_ms = (perf_counter() - getattr(g, "request_started_at", perf_counter())) * 1000
        request_id = getattr(g, "request_id", "-")
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "HTTP %s %s respondeu %s em %.1f ms. request_id=%s",
            request.method, request.path, response.status_code, elapsed_ms, request_id,
        )
        return response

    @app.errorhandler(HTTPException)
    def http_exception_handler(error):
        # API-001: respostas de erro em /api/* sempre no envelope JSON padrão,
        # preservando status e cabeçalhos relevantes (Allow/Retry-After).
        if not request.path.startswith("/api/"):
            return error
        code = (error.name or "HTTP_ERROR").upper().replace(" ", "_")
        response, status = err_json(code, error.description, status=error.code or 500)
        try:
            original_headers = dict(error.get_headers())
        except Exception:
            original_headers = {}
        for header in ("Allow", "Retry-After"):
            if header in original_headers:
                response.headers[header] = original_headers[header]
        return response, status

    @app.errorhandler(Exception)
    def unhandled_error(error):
        if isinstance(error, HTTPException):
            # Delegado ao handler acima (envelope JSON para /api/*).
            return http_exception_handler(error)
        logger.exception("Erro não tratado durante a requisição %s %s.", request.method, request.path)
        return err_json("INTERNAL_SERVER_ERROR", "Ocorreu um erro interno.", status=500)

    @app.errorhandler(RateLimitExceeded)
    def rate_handler(e):
        logger.warning("Limite de requisições atingido na rota %s.", request.path)
        return err_json(
            code="RATE_LIMITED",
            message="Muitas tentativas realizadas, tente novamente após 1 minuto",
            status=429,
        )

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=app.debug)
