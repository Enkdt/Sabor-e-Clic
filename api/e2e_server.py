"""Servidor Flask para testes end-to-end (Playwright).

Usa um banco de dados isolado e descartável (nunca o banco de desenvolvimento/demo),
semeia dados determinísticos e sobe na porta esperada pelo proxy do Vite.

Uso:
    DATABASE=/tmp/e2e.db .venv/bin/python e2e_server.py

Se DATABASE não for definido, cria um arquivo temporário próprio.
"""

import os
import tempfile

# Garante um banco isolado ANTES de importar a app/config.
if not os.environ.get("DATABASE"):
    fd, path = tempfile.mkstemp(prefix="sabor-e2e-", suffix=".db")
    os.close(fd)
    os.environ["DATABASE"] = path

# Ambiente de desenvolvimento (não produção) para o seed poder rodar.
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SECRET_KEY", "e2e-teste-chave-nao-sensivel-0123456789")

from app import app  # noqa: E402  (precisa vir depois de configurar o ambiente)
import seed_demo  # noqa: E402


def main():
    with app.app_context():
        seed_demo.seed()
    port = int(os.environ.get("E2E_PORT", "5000"))
    # use_reloader=False: um único processo, previsível para os testes.
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
