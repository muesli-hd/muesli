"""online tutorial indication

Revision ID: 5f63f9c40f95
Revises: 7aef24a65ac8
Create Date: 2020-11-06 14:38:28.677528

"""

# revision identifiers, used by Alembic.
revision = '5f63f9c40f95'
down_revision = '7aef24a65ac8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('allocation_criteria', sa.Column('indicates_online', sa.Boolean(), nullable=True))
    op.execute('UPDATE allocation_criteria SET indicates_online = False')
    op.alter_column('allocation_criteria', 'indicates_online', nullable=False)

def downgrade():
    op.drop_column('allocation_criteria', 'indicates_online')
