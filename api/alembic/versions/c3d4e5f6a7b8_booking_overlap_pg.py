"""booking overlap exclusion constraint for PostgreSQL (DATA-004)

Revision ID: c3d4e5f6a7b8
Revises: e1748ac76fb5
Create Date: 2026-11-11 16:30:00.000000

O baseline cria triggers SQLite que impedem sobreposição de agendamentos ACEITOS
na mesma bancada. Em PostgreSQL não há esses triggers; esta migração adiciona uma
EXCLUDE constraint (via btree_gist) que torna a invariante uma regra do banco —
duas requisições concorrentes não conseguem aceitar faixas sobrepostas.

Só roda em PostgreSQL; em SQLite/outros dialetos é no-op (as triggers já cobrem).
"""
from alembic import op


revision = 'c3d4e5f6a7b8'
down_revision = 'e1748ac76fb5'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    # Intervalo [horario_agendado, horario_agendado + tempo_agendado minutos).
    # Usa `tempo_agendado * interval '1 minute'` (IMMUTABLE) em vez de converter
    # texto para interval, que o Postgres recusa em expressão de índice.
    op.execute(
        """
        ALTER TABLE agendamento
        ADD CONSTRAINT excl_agendamento_overlap
        EXCLUDE USING gist (
            id_bancada WITH =,
            tsrange(
                horario_agendado,
                horario_agendado + (tempo_agendado * interval '1 minute')
            ) WITH &&
        )
        WHERE (status = 'aceito')
        """
    )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE agendamento DROP CONSTRAINT IF EXISTS excl_agendamento_overlap")
