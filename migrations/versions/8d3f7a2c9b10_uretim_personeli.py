"""uretim personeli

Revision ID: 8d3f7a2c9b10
Revises: 539ba0e7d6a7
Create Date: 2026-05-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '8d3f7a2c9b10'
down_revision = '539ba0e7d6a7'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'uretim_personeli' not in tables:
        op.create_table(
            'uretim_personeli',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('ad', sa.String(length=100), nullable=False),
            sa.Column('soyad', sa.String(length=100), nullable=True),
            sa.Column('istasyon_id', sa.Integer(), nullable=True),
            sa.Column('sicil_no', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['istasyon_id'], ['is_istasyonu.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('sicil_no')
        )

    uretim_kaydi_columns = {c['name'] for c in inspector.get_columns('uretim_kaydi')}
    if 'uretim_personeli_id' not in uretim_kaydi_columns:
        with op.batch_alter_table('uretim_kaydi', schema=None) as batch_op:
            batch_op.add_column(sa.Column('uretim_personeli_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                'fk_uretim_kaydi_uretim_personeli_id',
                'uretim_personeli',
                ['uretim_personeli_id'],
                ['id']
            )

    satir_columns = {c['name'] for c in inspector.get_columns('uretim_plani_satir')}
    with op.batch_alter_table('uretim_plani_satir', schema=None) as batch_op:
        if 'devir_adet' not in satir_columns:
            batch_op.add_column(sa.Column('devir_adet', sa.Integer(), nullable=True, server_default='0'))
        if 'kaynak' not in satir_columns:
            batch_op.add_column(sa.Column('kaynak', sa.String(length=20), nullable=True, server_default='plan'))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'uretim_plani_satir' in tables:
        satir_columns = {c['name'] for c in inspector.get_columns('uretim_plani_satir')}
        with op.batch_alter_table('uretim_plani_satir', schema=None) as batch_op:
            if 'kaynak' in satir_columns:
                batch_op.drop_column('kaynak')
            if 'devir_adet' in satir_columns:
                batch_op.drop_column('devir_adet')

    if 'uretim_kaydi' in tables:
        uretim_kaydi_columns = {c['name'] for c in inspector.get_columns('uretim_kaydi')}
        if 'uretim_personeli_id' in uretim_kaydi_columns:
            with op.batch_alter_table('uretim_kaydi', schema=None) as batch_op:
                batch_op.drop_constraint('fk_uretim_kaydi_uretim_personeli_id', type_='foreignkey')
                batch_op.drop_column('uretim_personeli_id')

    if 'uretim_personeli' in tables:
        op.drop_table('uretim_personeli')
