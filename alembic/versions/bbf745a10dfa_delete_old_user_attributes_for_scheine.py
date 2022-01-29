"""delete old user attributes for scheine

Revision ID: bbf745a10dfa
Revises: b759946a1129
Create Date: 2020-10-26 19:25:49.431329

"""

# revision identifiers, used by Alembic.
revision = 'bbf745a10dfa'
down_revision = 'b759946a1129'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('users', 'birth_place')
    op.drop_column('users', 'birth_date')

def downgrade():
    op.add_column('users', sa.Column('birth_place', sa.Text))
    op.add_column('users', sa.Column('birth_date', sa.Text))
