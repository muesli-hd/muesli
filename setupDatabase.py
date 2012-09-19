import muesli
import muesli.models as models
import sqlalchemy as sa

import sys

engine = muesli.engine()
if len(sys.argv)==1:
	models.Base.metadata.create_all(engine)
else:
	admin_user_mail = sys.argv[1]
	import muesli.models as models
	from muesli.models import *
	import sqlalchemy as sa
	models.initializeSession(engine)
	session = models.Session()
	user = session.query(User).filter(User.email==admin_user_mail).one()
	user.is_admin = True
	session.commit()
	print "%s is admin now" % admin_user_mail
