"""merge the two alembic heads due to the merge of PR's #66 & ##67

Revision ID: d3d8e4c5a116
Revises: ('26162cefdac7', '8c2d5633e0d2')
Create Date: 2019-02-20 18:40:56.718910

"""

# revision identifiers, used by Alembic.
revision = 'd3d8e4c5a116'
down_revision = ('26162cefdac7', '8c2d5633e0d2')

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass

def downgrade():
    pass
