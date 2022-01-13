# This file is for manual importing in python command line sessions. It is not used elsewhere in the codebase

import sqlalchemy
from . import models

engine = sqlalchemy.create_engine('postgresql:///muesli', echo=False)
Session = sqlalchemy.orm.sessionmaker(bind=engine)
session = Session()
#print(session.query(models.User).all())
