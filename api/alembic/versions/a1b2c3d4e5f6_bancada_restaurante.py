"""bancada ownership: add bancada.id_restaurante (SEC-002)

Revision ID: a1b2c3d4e5f6
Revises: 8c5ce5754122
Create Date: 2026-11-11 15:40:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '8c5ce5754122'
branch_labels = None
depends_on = None


def upgrade():
    # Coluna nullable: bancadas legadas sem dono ficam como admin-only (SEC-002).
    with op.batch_alter_table('bancada', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_restaurante', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_bancada_restaurante', 'restaurante', ['id_restaurante'], ['id']
        )


def downgrade():
    with op.batch_alter_table('bancada', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bancada_restaurante', type_='foreignkey')
        batch_op.drop_column('id_restaurante')
