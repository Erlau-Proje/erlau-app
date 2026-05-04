"""y001_user_permission_matrix

Revision ID: 9b2c4d6e8f10
Revises: 657e2789fa39
Create Date: 2026-05-03 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '9b2c4d6e8f10'
down_revision = '657e2789fa39'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'user_permission' not in inspector.get_table_names():
        op.create_table(
            'user_permission',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('permission_code', sa.String(length=80), nullable=False),
            sa.Column('allowed', sa.Boolean(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('updated_by_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['updated_by_id'], ['user.id']),
            sa.ForeignKeyConstraint(['user_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'permission_code', name='uq_user_permission_code'),
        )
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('user_permission')} if 'user_permission' in inspector.get_table_names() else set()
    if op.f('ix_user_permission_permission_code') not in existing_indexes:
        op.create_index(op.f('ix_user_permission_permission_code'), 'user_permission', ['permission_code'], unique=False)
    if op.f('ix_user_permission_user_id') not in existing_indexes:
        op.create_index(op.f('ix_user_permission_user_id'), 'user_permission', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_user_permission_user_id'), table_name='user_permission')
    op.drop_index(op.f('ix_user_permission_permission_code'), table_name='user_permission')
    op.drop_table('user_permission')
