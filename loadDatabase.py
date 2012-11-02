import muesli
import muesli.models as models
from muesli.models import *
import sqlalchemy as sa
engine = sa.create_engine('postgresql:///muesli')
muesli.engine = lambda: engine
models.initializeSession(engine)
session = models.Session()

def correctSubjects(old, new):
	us = session.query(models.User).filter(models.User.subject == old).all()
	for u in us:
		print u
	answer = raw_input("Change subject to %s? (y/N)" % new).lower()
	if answer == 'y':
		for u in us:
			u.subject = new
			print "Changed", u
	print "Do not forget to commit"
	

print "A muesli-session has been initialized as 'session'"
print "The muesli models have been included via 'models'"
