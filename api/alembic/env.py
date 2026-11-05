"""Ambiente do Alembic, integrado ao app Flask.

A URL do banco e o metadata são obtidos do próprio app (config + models), evitando
duplicar connection string. Suporta execução offline e online.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from config import Config
import models  # noqa: F401 — importa os modelos para popular o metadata
from extensions import db

config = context.config
# A URL pode já ter sido definida por quem chamou (run_migrations passa a do app atual).
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", Config.SQLALCHEMY_DATABASE_URI)

# Só aplica o logging do alembic.ini em execução via CLI (offline/standalone); quando chamado
# de dentro do app (online), preserva o logging já configurado pela aplicação/testes.
if config.config_file_name is not None and context.is_offline_mode():
    fileConfig(config.config_file_name)

target_metadata = db.metadata


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,  # SQLite: habilita ALTER via tabela temporária
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite: ALTER COLUMN/constraints via batch
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
