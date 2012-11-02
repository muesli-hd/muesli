import muesli
import muesli.models as models
from muesli.models import *
import sqlalchemy as sa
engine = sa.create_engine('postgresql:///muesli')
muesli.engine = lambda: engine
models.initializeSession(engine)
session = models.Session()
print "A muesli-session has been initialized as 'session'"
print "The muesli models have been included via 'models'"
