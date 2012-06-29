%run loadDatabase.py
u = session.query(models.User).filter(User.last_name==u'Kümmerer').one()
from hashlib import sha1
u.password = sha1('test').hexdigest()
for i,u2 in enumerate(session.query(models.User).all()):
	if not u2.id == u.id:
		u2.email = str(i)
session.commit()
