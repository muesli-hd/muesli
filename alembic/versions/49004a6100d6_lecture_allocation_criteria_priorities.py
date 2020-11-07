"""lecture_allocation_criteria_priorities

Revision ID: 49004a6100d6
Revises: 5f63f9c40f95
Create Date: 2020-11-07 15:03:46.263189

"""

# revision identifiers, used by Alembic.
revision = '49004a6100d6'
down_revision = '5f63f9c40f95'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('lecture_allocation_criteria_pkey', 'lecture_allocation_criteria', type_='primary')
    op.create_primary_key('lecture_allocation_criteria_pkey', 'lecture_allocation_criteria', ['lecture', 'criterion', 'priority'])

def downgrade():
    op.drop_constraint('lecture_allocation_criteria_pkey', 'lecture_allocation_criteria', type_='primary')
    op.create_primary_key('lecture_allocation_criteria_pkey', 'lecture_allocation_criteria', ['lecture', 'criterion'])
