import sys

import muesli
import muesli.models as models

engine = muesli.engine()
if len(sys.argv) == 1:
    from alembic.config import Config
    from alembic import command

    models.Base.metadata.create_all(engine)
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, "head")
else:
    admin_user_mail = sys.argv[1]
    import muesli.models as models
    from muesli.models import *
    import sqlalchemy as sa

    models.initializeSession(engine)
    session = models.Session()
    user = session.query(User).filter(User.email == admin_user_mail).one()
    user.is_admin = 1
    session.commit()
    print("%s is admin now" % admin_user_mail)
