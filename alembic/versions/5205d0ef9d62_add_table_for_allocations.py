"""Add table for allocations

Revision ID: 5205d0ef9d62
Revises: d3d8e4c5a116
Create Date: 2020-10-15 00:28:08.891286

"""

# revision identifiers, used by Alembic.
revision = '5205d0ef9d62'
down_revision = 'd3d8e4c5a116'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'allocations',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('state', sa.Text, nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'allocation_time_preferences',
        sa.Column('allocation', sa.Integer, sa.ForeignKey("allocations.id", ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column('student', sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column('time', sa.String(7), primary_key=True),
        sa.Column('penalty', sa.Integer, nullable=False),
    )
    op.create_table(
        'allocation_criteria',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('allocation', sa.Integer, sa.ForeignKey("allocations.id", ondelete="CASCADE"), nullable=False),
        sa.Column('name', sa.Text),
        sa.Column('penalty', sa.Integer)
    )
    op.create_table(
        'allocation_criteria_options',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('criterion', sa.Integer, sa.ForeignKey('allocation_criteria.id', ondelete="CASCADE")),
        sa.Column('name', sa.Text),
        sa.Column('order_number', sa.Integer, nullable=False),
        sa.Column('penalty', sa.Integer, nullable=False)
    )
    op.create_table(
        'student_allocation_criteria',
        sa.Column('criterion', sa.Integer, sa.ForeignKey('allocation_criteria.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('student', sa.Integer, sa.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('option', sa.Integer, sa.ForeignKey('allocation_criteria_options.id', ondelete="CASCADE"))
    )
    op.create_table(
        'tutorial_allocation_criteria',
        sa.Column('tutorial', sa.Integer, sa.ForeignKey('tutorials.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('criterion', sa.Integer, sa.ForeignKey('allocation_criteria.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('penalty', sa.Integer)
    )
    op.create_table(
        'allocation_students',
        sa.Column('allocation', sa.Integer, sa.ForeignKey('allocations.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('student', sa.Integer, sa.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('lecture', sa.Integer, sa.ForeignKey('lectures.id', ondelete='CASCADE'), primary_key=True)
    )
    op.add_column('tutorials', sa.Column('allocation', sa.Integer, sa.ForeignKey('allocations.id', ondelete="CASCADE"), default=None))
    op.add_column('tutorials', sa.Column('video_call', sa.Text))
    op.drop_table('tutorial_preferences')

def downgrade():
    op.drop_column('tutorials', 'allocation')
    op.drop_column('tutorials', 'video_call')
    op.drop_table('allocation_students')
    op.drop_table('allocation_time_preferences')
    op.drop_table('student_allocation_criteria')
    op.drop_table('tutorial_allocation_criteria')
    op.drop_table('allocation_criteria_options')
    op.drop_table('allocation_criteria')
    op.drop_table('allocations')
    op.create_table(
        'tutorial_preferences',
        sa.Column('lecture', sa.Integer, sa.ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column('student', sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column('tutorial', sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column('penalty', sa.Integer, nullable=False),
    )
