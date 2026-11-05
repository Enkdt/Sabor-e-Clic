"""Execução das migrações do Alembic no boot do app.

Mantém o app.py enxuto: ele só chama `run_migrations(app)`. O esquema é definido pelas
migrações em `alembic/versions/` (geradas com `op.*`), não por SQL espalhado no bootstrap.

Regra de boot:
- Banco novo (sem tabelas): aplica todas as migrações (`upgrade head`).
- Banco já existente de uma versão anterior sem controle do Alembic: marca a baseline
  como aplicada (`stamp`) e então sobe o que faltar, sem recriar o que já existe.
- Banco já versionado: apenas `upgrade head`.
"""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent
BASELINE_REVISION = "8c5ce5754122"


def _alembic_config():
    cfg = AlembicConfig(str(_BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BASE_DIR / "alembic"))
    return cfg


def run_migrations(app):
    with app.app_context():
        from extensions import db
        try:
            cfg = _alembic_config()
            # Usa a URI real DESTE app (respeita overrides de teste), não só a do Config padrão.
            cfg.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])
            with db.engine.connect() as conn:
                versao_atual = MigrationContext.configure(conn).get_current_revision()
            tabelas = set(inspect(db.engine).get_table_names())

            if versao_atual is None and tabelas - {"alembic_version"}:
                # Banco pré-Alembic já com o esquema atual: adota a baseline sem recriar tabelas.
                command.stamp(cfg, BASELINE_REVISION)
                logger.info("Banco existente adotado pelo Alembic (stamp baseline).")

            command.upgrade(cfg, "head")
            cabeca = ScriptDirectory.from_config(cfg).get_current_head()
            logger.info("Migrações aplicadas; versão atual: %s.", cabeca)
        except Exception:
            logger.exception("Falha ao executar as migrações do banco de dados.")
            raise
