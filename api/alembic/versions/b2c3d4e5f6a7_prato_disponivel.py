"""dish availability: add prato.disponivel (DATA-003)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-11 15:55:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Pratos existentes ficam disponíveis por padrão.
    # server_default precisa ser portável: 'true'/'false' valem em PostgreSQL e
    # SQLite (que aceita o literal booleano). '1' falha no Postgres (tipo boolean).
    with op.batch_alter_table('prato', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('disponivel', sa.Boolean(), nullable=False, server_default=sa.text('true'))
        )


def downgrade():
    with op.batch_alter_table('prato', schema=None) as batch_op:
        batch_op.drop_column('disponivel')
