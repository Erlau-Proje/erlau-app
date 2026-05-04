"""fason_urun_fiyat_tablolari

Revision ID: aab61f295db3
Revises: 9b2c4d6e8f10
Create Date: 2026-05-04 05:59:53.291513

"""
from alembic import op
import sqlalchemy as sa


revision = 'aab61f295db3'
down_revision = '9b2c4d6e8f10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('fason_urun',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tedarikci_id', sa.Integer(), nullable=False),
        sa.Column('urun_adi', sa.String(length=300), nullable=False),
        sa.Column('urun_kodu', sa.String(length=100), nullable=True),
        sa.Column('birim', sa.String(length=20), nullable=True),
        sa.Column('aciklama', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tedarikci_id'], ['tedarikci.id'], name='fk_fason_urun_tedarikci'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('fason_urun', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_fason_urun_tedarikci_id'), ['tedarikci_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_fason_urun_urun_adi'), ['urun_adi'], unique=False)

    op.create_table('fason_fiyat',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fason_urun_id', sa.Integer(), nullable=False),
        sa.Column('fiyat', sa.Float(), nullable=False),
        sa.Column('para_birimi', sa.String(length=10), nullable=True),
        sa.Column('tarih', sa.Date(), nullable=False),
        sa.Column('notlar', sa.Text(), nullable=True),
        sa.Column('giren_personel_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['fason_urun_id'], ['fason_urun.id'], name='fk_fason_fiyat_urun'),
        sa.ForeignKeyConstraint(['giren_personel_id'], ['user.id'], name='fk_fason_fiyat_personel'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('fason_fiyat')
    with op.batch_alter_table('fason_urun', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fason_urun_urun_adi'))
        batch_op.drop_index(batch_op.f('ix_fason_urun_tedarikci_id'))
    op.drop_table('fason_urun')
