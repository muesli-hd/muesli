"""Add tables for storing subjects and their mapping to students

Revision ID: 8025dec50f89
Revises: 49004a6100d6
Create Date: 2021-08-15 14:31:40.721068

"""

# revision identifiers, used by Alembic.
import muesli.models

revision = '8025dec50f89'
down_revision = '49004a6100d6'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def upgrade():
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('name', sa.Text, nullable=False, unique=True),
        sa.Column('approved', sa.Boolean, nullable=False),
    )
    op.create_table(
        'user_subjects',
        sa.Column('student', sa.Integer, sa.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('subject', sa.Integer, sa.ForeignKey('subjects.id', ondelete="CASCADE"), primary_key=True),
    )

    # Insert the subjects that were previously defined in the config file
    bind = op.get_bind()
    #bind = op.get_bind().execution_options(isolation_level="READ UNCOMMITTED")
    session = sa.orm.Session(bind=bind)

    subject_map = {}

    # Add approved subjects
    for name in [
        "Mathematik (BSc 100%)",
        "Mathematik (BSc 50%)",
        "Mathematik (MSc)",
        "Informatik (BSc 100%)",
        "Informatik (BSc 50%)",
        "Informatik (MSc)",
        "Physik (BSc 100%)",
        "Physik (BSc 50%)",
        "Physik (MSc)",
        "Scientific Computing (MSc)",
        "Computerlinguistik (BA 100%)",
        "Computerlinguistik (BA 50%)",
    ]:
        subject = muesli.models.Subject()
        subject.name = name
        subject.approved = True
        session.add(subject)
        subject_map[name] = subject

    # Migrate existing users
    users = session.scalars(sa.select(muesli.models.User))
    for user in users:
        if not user.subject:
            continue
        if user.subject not in subject_map:
            subject = muesli.models.Subject()
            subject.name = user.subject
            subject.approved = False
            session.add(subject)
            subject_map[user.subject] = subject
        user.subjects.append(subject_map[user.subject])
    session.commit()
    # In production there is a view, some admin created back when a lot of things were done manually.
    # Remove it, if it exists.
    if sa.inspect(bind).has_table('common_statistics'):
        op.execute('DROP VIEW common_statistics')
    op.drop_column('users', 'subject')


def downgrade():
    op.add_column('users', sa.Column('subject', sa.Text))

    # Migrate data
    session = sa.orm.Session(bind=op.get_bind())
    for user in session.scalars(sa.select(muesli.models.User)):
        user_subjects = user.subjects
        if len(user.subjects) > 0:
            user.subject = user.subjects[0].name
    session.commit()

    # drop tables
    op.drop_table('user_subjects')
    op.drop_table('subjects')
