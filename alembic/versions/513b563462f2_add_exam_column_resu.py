"""Add Exam-Column results_hidden

Revision ID: 513b563462f2
Revises: None
Create Date: 2012-02-02 22:55:00.909572

"""

# revision identifiers, used by Alembic.
revision = '513b563462f2'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('exams', sa.Column('results_hidden', sa.Boolean, default=False))

def downgrade():
    op.drop_colum('exams', 'results_hidden')
