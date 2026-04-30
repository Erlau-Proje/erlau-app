"""teklif_grubu batch_id

Revision ID: 539ba0e7d6a7
Revises: dfd6d2c51497
Create Date: 2026-04-29 15:59:37.033367

"""
from alembic import op
import sqlalchemy as sa


revision = '539ba0e7d6a7'
down_revision = 'dfd6d2c51497'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('teklif_grubu', schema=None) as batch_op:
        batch_op.add_column(sa.Column('batch_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_teklif_grubu_batch_id', ['batch_id'], unique=False)


def downgrade():
    with op.batch_alter_table('teklif_grubu', schema=None) as batch_op:
        batch_op.drop_index('ix_teklif_grubu_batch_id')
        batch_op.drop_column('batch_id')
