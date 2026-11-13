"""Servidor Flask para testes end-to-end (Playwright).

Usa um banco de dados isolado e descartável (NUNCA o banco de desenvolvimento/
produção), semeia dados determinísticos e sobe na porta esperada pelo proxy do
Vite.

Isolamento (TEST-001): definimos DATABASE_URL para um SQLite temporário ANTES de
importar app/config. Isso sobrepõe qualquer DATABASE_URL de produção presente no
ambiente/.env. O servidor recusa iniciar se o DATABASE_URL efetivo não for um
SQLite descartável.

Uso:
    python e2e_server.py
    E2E_DB=/tmp/e2e.db python e2e_server.py   # caminho explícito opcional
"""

import os
import tempfile

# Banco isolado ANTES de importar app/config. Força SQLite temporário e ignora
# qualquer DATABASE_URL de produção herdado do ambiente.
_e2e_db = os.environ.get("E2E_DB")
if not _e2e_db:
    fd, _e2e_db = tempfile.mkstemp(prefix="sabor-e2e-", suffix=".db")
    os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_e2e_db}"
os.environ["DATABASE"] = _e2e_db

# Ambiente de teste (não produção) para o seed poder rodar e para evitar os
# guards de produção que exigiriam Postgres/HTTPS.
os.environ["APP_ENV"] = "test"
os.environ.setdefault("SECRET_KEY", "e2e-teste-chave-nao-sensivel-0123456789abcd")
os.environ.setdefault("SESSION_COOKIE_SECURE", "0")
os.environ.setdefault("FRONTEND_BASE_URL", "http://localhost:5173")
# E2E executa muitos logins/requisições em sequência contra um banco descartável;
# os limites de produção (ex.: 5 logins/min) derrubariam a suíte com 429. Definido
# ANTES de importar app/config para que o Flask-Limiter já inicie desabilitado.
# Afeta APENAS este servidor de teste isolado (nunca produção).
os.environ["RATELIMIT_ENABLED"] = "0"

from app import create_app  # noqa: E402  (precisa vir depois de configurar o ambiente)
from migrations import run_migrations  # noqa: E402
import seed_demo  # noqa: E402

app = create_app()


def _assert_disposable_db():
    uri = app.config.get("SQLALCHEMY_DATABASE_URI") or ""
    if not uri.startswith("sqlite"):
        raise RuntimeError(
            "E2E recusado: o banco efetivo não é um SQLite descartável (%r)." % uri
        )


def main():
    _assert_disposable_db()
    # Cria o esquema explicitamente (migrações não rodam mais no boot do app).
    run_migrations(app)
    with app.app_context():
        seed_demo.seed()
    port = int(os.environ.get("E2E_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
