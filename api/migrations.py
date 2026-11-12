"""Ciclo de vida das migrações do Alembic (PROD-002).

As migrações NÃO rodam mais na criação do app (ver app.py). Rode-as uma vez por
release, via CLI, com a mesma configuração do app:

    python migrations.py upgrade     # aplica tudo até head (uso em release/CI)
    python migrations.py current     # mostra a revisão atual do banco
    python migrations.py stamp-head  # marca head sem rodar DDL (adoção de baseline)

Regra de boot preservada em `run_migrations`:
- Banco pré-Alembic já com o esquema atual: adota a baseline sem recriar tabelas.
- Caso contrário: apenas `upgrade head`.
"""
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent
BASELINE_REVISION = "8c5ce5754122"


def _alembic_config(database_uri: str):
    cfg = AlembicConfig(str(_BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BASE_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_uri)
    return cfg


def run_migrations(app):
    """Aplica as migrações para o banco deste app. Uso: comando de release/CI.

    Deve ser chamado explicitamente (nunca na importação do app).
    """
    with app.app_context():
        from extensions import db
        try:
            cfg = _alembic_config(app.config["SQLALCHEMY_DATABASE_URI"])
            with db.engine.connect() as conn:
                versao_atual = MigrationContext.configure(conn).get_current_revision()
            tabelas = set(inspect(db.engine).get_table_names())

            if versao_atual is None and tabelas - {"alembic_version"}:
                command.stamp(cfg, BASELINE_REVISION)
                logger.info("Banco existente adotado pelo Alembic (stamp baseline).")

            command.upgrade(cfg, "head")
            cabeca = ScriptDirectory.from_config(cfg).get_current_head()
            logger.info("Migrações aplicadas; versão atual: %s.", cabeca)
        except Exception:
            logger.exception("Falha ao executar as migrações do banco de dados.")
            raise


def init_test_schema(app):
    """Cria o esquema completo (incluindo triggers do Alembic) para um app de teste.

    Usa a migração baseline contra o SQLite de teste, garantindo paridade com
    produção (ex.: trigger de sobreposição de agendamento). NUNCA deve ser
    chamado fora de um app de teste/SQLite.
    """
    uri = app.config.get("SQLALCHEMY_DATABASE_URI") or ""
    if not app.config.get("TESTING"):
        raise RuntimeError("init_test_schema só pode ser usado com TESTING=True.")
    if not uri.startswith("sqlite"):
        raise RuntimeError("init_test_schema só suporta SQLite de teste.")
    cfg = _alembic_config(uri)
    with app.app_context():
        command.upgrade(cfg, "head")


def _build_app():
    from app import create_app
    return create_app()


def _cmd_upgrade():
    app = _build_app()
    run_migrations(app)
    print("Migrações aplicadas até head.")


def _cmd_current():
    app = _build_app()
    with app.app_context():
        from extensions import db
        with db.engine.connect() as conn:
            rev = MigrationContext.configure(conn).get_current_revision()
    print(f"Revisão atual: {rev}")


def _cmd_stamp_head():
    app = _build_app()
    cfg = _alembic_config(app.config["SQLALCHEMY_DATABASE_URI"])
    with app.app_context():
        command.stamp(cfg, "head")
    print("Banco marcado (stamp) em head.")


_COMMANDS = {
    "upgrade": _cmd_upgrade,
    "current": _cmd_current,
    "stamp-head": _cmd_stamp_head,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in _COMMANDS:
        print("Uso: python migrations.py {upgrade|current|stamp-head}", file=sys.stderr)
        return 2
    logging.basicConfig(level=logging.INFO)
    _COMMANDS[argv[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
