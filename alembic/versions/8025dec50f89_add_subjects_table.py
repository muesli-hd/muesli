"""Add tables for storing subjects and their mapping to students

Revision ID: 8025dec50f89
Revises: 49004a6100d6
Create Date: 2021-08-15 14:31:40.721068

"""

# revision identifiers, used by Alembic.
revision = '8025dec50f89'
down_revision = '49004a6100d6'

from muesli.models import Subject, User
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
        subject = Subject()
        subject.name = name
        subject.approved = True
        session.add(subject)
        subject_map[name] = subject

    # Migrate existing users
    def append_subject(subject_name):
        if subject_name not in subject_map:
            subject = Subject()
            subject.name = subject_name
            subject.approved = False
            session.add(subject)
            subject_map[subject_name] = subject
        user.subjects.append(subject_map[subject_name])

    users = session.scalars(sa.select(User))
    for user in users:
        if user.subject:
            append_subject(user.subject)
        if user.second_subject:
            append_subject(f'LA Beifach: {user.second_subject}')
    session.commit()
    # In production there is a view, some admin created back when a lot of things were done manually.
    # Remove it, if it exists.
    if sa.inspect(bind).has_table('common_statistics'):
        op.execute('DROP VIEW common_statistics')
    op.drop_column('users', 'subject')
    op.drop_column('users', 'second_subject')


def downgrade():
    op.add_column('users', sa.Column('subject', sa.Text))
    op.add_column('users', sa.Column('second_subject', sa.Text))

    # Migrate data
    session = sa.orm.Session(bind=op.get_bind())
    for user in session.scalars(sa.select(User)):
        user_subjects = user.subjects
        if user.subjects.count() > 0:
            for s in user.subjects:
                if s.name.startswith('LA Beifach: '):
                    user.second_subject = s.name[12:]
                    break
            for s in user_subjects:
                if not s.name.startswith('LA Beifach: '):
                    user.subject = s.name
                    break
    session.commit()

    # drop tables
    op.drop_table('user_subjects')
    op.drop_table('subjects')
