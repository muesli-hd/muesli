"""user_has_updated

Revision ID: 26162cefdac7
Revises: caab371ebc9f
Create Date: 2019-02-19 17:48:49.408174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26162cefdac7'
down_revision = 'caab371ebc9f'


def upgrade():
    op.create_table(
        'user_has_updated',
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('has_updated_info', sa.String, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id'),
    )


def downgrade():
    op.drop_table('user_has_updated')