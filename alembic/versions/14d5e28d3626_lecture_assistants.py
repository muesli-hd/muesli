"""lecture_assistants

Revision ID: 14d5e28d3626
Revises: 2a1638d875ac
Create Date: 2012-04-13 11:50:50.501793

"""

# revision identifiers, used by Alembic.
revision = '14d5e28d3626'
down_revision = '2a1638d875ac'

import sqlalchemy as sa

from alembic import op


def upgrade():
    ### Caution: Only works in online mode!!!
    op.create_table('lecture_assistants',
                    sa.Column('lecture', sa.Integer(), nullable=False),
                    sa.Column('assistant', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['assistant'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['lecture'], ['lectures.id'], ),
                    sa.PrimaryKeyConstraint('lecture', 'assistant')
                    )
    lectures = sa.sql.table('lectures',
                            sa.Column('id', sa.Integer),
                            sa.Column('assistant', sa.Integer)
                            )
    connection = op.get_bind()
    results = connection.execute(lectures.select())
    ins = []
    for res in results:
        if res.assistant != None:
            ins.append({'lecture': res.id, 'assistant': res.assistant})
    lecture_assistants = sa.sql.table('lecture_assistants',
                                      sa.Column('lecture', sa.Integer(), nullable=False),
                                      sa.Column('assistant', sa.Integer(), nullable=False)
                                      )
    if ins:
        op.bulk_insert(lecture_assistants, ins)


def downgrade():
    lecture_assistants = sa.sql.table('lecture_assistants',
                                      sa.Column('lecture', sa.Integer(), nullable=False),
                                      sa.Column('assistant', sa.Integer(), nullable=False)
                                      )
    lectures = sa.sql.table('lectures',
                            sa.Column('id', sa.Integer),
                            sa.Column('assistant', sa.Integer)
                            )
    connection = op.get_bind()
    results = connection.execute(lecture_assistants.select())
    for res in results:
        connection.execute(lectures.update().where(lectures.c.id == res.lecture).values(assistant=res.assistant))
    op.drop_table('lecture_assistants')
