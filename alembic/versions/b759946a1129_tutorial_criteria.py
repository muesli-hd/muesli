"""tutorial_criteria

Revision ID: b759946a1129
Revises: 5205d0ef9d62
Create Date: 2020-10-21 17:36:58.999012

"""

# revision identifiers, used by Alembic.
revision = 'b759946a1129'
down_revision = '5205d0ef9d62'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('allocation_criteria', sa.Column('preferences_unnecessary', sa.Boolean, default=False, nullable=True))
    op.execute('UPDATE allocation_criteria SET preferences_unnecessary = FALSE')
    op.alter_column('allocation_criteria', 'preferences_unnecessary', nullable=False)
    op.create_table(
        'lecture_allocation_criteria',
        sa.Column('lecture', sa.Integer, sa.ForeignKey('lectures.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('criterion', sa.Integer, sa.ForeignKey('allocation_criteria.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('penalty', sa.Integer)
    )

def downgrade():
    op.drop_table('lecture_allocation_criteria')
    op.drop_column('allocation_criteria', 'preferences_unnecessary')
