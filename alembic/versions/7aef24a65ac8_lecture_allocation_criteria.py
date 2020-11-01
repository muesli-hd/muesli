"""Lecture allocation criteria

Revision ID: 7aef24a65ac8
Revises: bbf745a10dfa
Create Date: 2020-11-01 17:41:30.596854

"""

# revision identifiers, used by Alembic.
revision = '7aef24a65ac8'
down_revision = 'bbf745a10dfa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('lecture_allocation_criteria', sa.Column('priority', sa.Integer(), nullable=True))
    op.execute('UPDATE lecture_allocation_criteria SET priority = 0')
    op.alter_column('lecture_allocation_criteria', 'priority', nullable=False)
    op.alter_column('lecture_allocation_criteria', 'penalty', new_column_name='min_penalty')
    op.execute('UPDATE lecture_allocation_criteria SET min_penalty = 0 WHERE min_penalty IS NULL')
    op.alter_column('lecture_allocation_criteria', 'min_penalty', nullable=False)

def downgrade():
    op.alter_column('lecture_allocation_criteria', 'min_penalty', new_column_name='penalty')
    op.drop_column('lecture_allocation_criteria', 'priority')
