"""Add tables for storing subjects and their mapping to students

Revision ID: 8025dec50f89
Revises: 49004a6100d6
Create Date: 2021-08-15 14:31:40.721068

"""

# revision identifiers, used by Alembic.
revision = '8025dec50f89'
down_revision = '49004a6100d6'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.automap import automap_base
import sqlalchemy.orm

Base = automap_base()


def upgrade():
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('name', sa.Text, nullable=False, unique=True),
        sa.Column('curated', sa.Boolean, nullable=False),
    )
    op.create_table(
        'user_subjects',
        sa.Column('student', sa.Integer, sa.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('subject', sa.Integer, sa.ForeignKey('subjects.id', ondelete="CASCADE"), primary_key=True),
    )

    # Insert the subjects that were previously defined in the config file
    bind = op.get_bind()

    # Due to clashing relationship names, we use this hack here
    def _gen_relationship(base, direction, return_fn,
                          attrname, local_cls, referred_cls, **kw):
        return sa.ext.automap.generate_relationship(base, direction, return_fn,
                                     attrname + '_ref', local_cls, referred_cls, **kw)

    session = sa.orm.Session(bind=bind)
    Base.prepare(bind, reflect=True, generate_relationship=_gen_relationship)

    subject_map = {}

    # Add curated subjects
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
        subject = Base.classes.subjects(name=name, curated=True)
        session.add(subject)
        subject_map[name] = subject

    # Migrate existing users
    def append_subject(subject_name):
        if subject_name not in subject_map:
            subject = Base.classes.subjects(name=subject_name, curated=False)
            session.add(subject)
            subject_map[subject_name] = subject
        # user.subjects is actually user.subjects_collection_ref in this case, due to auto mapping
        user.subjects_collection_ref.append(subject_map[subject_name])

    users = session.scalars(sa.select(Base.classes.users))
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
    for user in session.scalars(sa.select(Base.classes.users)):
        user_subjects = user.subjects_collection_ref
        for s in user_subjects:
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
