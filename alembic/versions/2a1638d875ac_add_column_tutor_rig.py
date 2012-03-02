"""Add column tutor_rights to lectures

Revision ID: 2a1638d875ac
Revises: 513b563462f2
Create Date: 2012-03-02 15:53:59.489507

"""

# revision identifiers, used by Alembic.
revision = '2a1638d875ac'
down_revision = '513b563462f2'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


lectures = table('lectures', 
    column('tutor_rights', sa.Text)
)

def upgrade():
    op.add_column('lectures', sa.Column('tutor_rights', sa.Text, nullable=False, default='editOwnTutorial', server_default='editOwnTutorial'))
	

def downgrade():
    op.drop_colum('lectures', 'tutor_rights')
