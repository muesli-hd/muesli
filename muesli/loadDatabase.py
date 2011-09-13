import sqlalchemy
import models

engine = sqlalchemy.create_engine('postgresql:///muesli', echo=False)
Session = sqlalchemy.orm.sessionmaker(bind=engine)
session = Session()
#print session.query(models.User).all()

