# -*- coding: utf-8 -*-
#
# muesli/tests/functionalTests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2011, Matthias Kuemmerer <matthias (at) matthias-k.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from hashlib import sha1

import unittest
import muesli.web

class OrigDatabaseTests(unittest.TestCase):
	def setUp(self):
		import muesli.web
		from muesli.web import main
		app = main({})
		from webtest import TestApp
		self.testapp = TestApp(app)

	def test_root(self):
		#session = muesli.models.Session()
		#print "Anzahl lectures", session.query(muesli.models.Lecture).count()
		res = self.testapp.get('/lecture/list', status=200)
		self.failUnless('Liste' in res.body)
	
	def test_login(self):
		res = self.testapp.get('/user/login', status=200)
		self.failUnless(True)

class BaseTests(unittest.TestCase):
	def setUp(self):
		import muesli
		import sqlalchemy
		self.engine = sqlalchemy.create_engine('sqlite:///:memory:')
		import muesli.models
		muesli.models.Base.metadata.create_all(self.engine)
		muesli.old_engine = muesli.engine
		muesli.engine = lambda: self.engine
		import muesli.web
		from muesli.web import main
		app = main({})
		from webtest import TestApp
		self.testapp = TestApp(app)
		self.session = muesli.models.Session()
		self.populate()

	def tearDown(self):
		muesli.engine = muesli.old_engine

	def populate(self):
		pass

	def test_start(self):
		res = self.testapp.get('/start', status=302)

	def test_admin(self):
		res = self.testapp.get('/admin', status=403)

	def test_user_login(self):
		res = self.testapp.get('/user/login', status=200)
	
	def test_user_logout(self):
		res = self.testapp.get('/user/logout', status=302)

	def test_user_list(self):
		res = self.testapp.get('/user/list', status=403)

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % 1234, status=404)

	def test_lecture_list(self):
		res = self.testapp.get('/lecture/list', status=200)

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/view/%s' % 12456, status=404)

	def test_lecture_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % 123456, status=404)



def setUserPassword(user, password):
	user.realpassword = password
	user.password = sha1(password).hexdigest()

class UnloggedTests(BaseTests):
	def populate(self):
		self.user = muesli.models.User()
		self.user.first_name = u'Stefan'
		self.user.last_name = u'Student'
		self.user.email = 'user@muesli.org'
		setUserPassword(self.user, 'userpassword')
		self.session.add(self.user)
		self.session.commit()

		self.user2 = muesli.models.User()
		self.user2.first_name = u'Sigmund'
		self.user2.last_name = u'Student'
		self.user2.email = 'user2@muesli.org'
		setUserPassword(self.user2, 'user2password')
		self.session.add(self.user2)
		self.session.commit()

		self.tutor = muesli.models.User()
		self.tutor.first_name = u'Thorsten'
		self.tutor.last_name = u'Tutor'
		self.tutor.email = 'tutor@muesli.org'
		setUserPassword(self.tutor, 'tutorpassword')
		self.session.add(self.tutor)
		self.session.commit()

		self.assistant = muesli.models.User()
		self.assistant.first_name = u'Armin'
		self.assistant.last_name = u'Assistent'
		self.assistant.email = 'assistant@muesli.org'
		setUserPassword(self.assistant, 'assistantpassword')
		self.assistant.is_assistant=True
		self.session.add(self.assistant)
		self.session.commit()

		self.assistant2 = muesli.models.User()
		self.assistant2.first_name = u'Armin'
		self.assistant2.last_name = u'Assistent2'
		self.assistant2.email = 'assistant2@muesli.org'
		setUserPassword(self.assistant2, 'assistant2password')
		self.assistant2.is_assistant=True
		self.session.add(self.assistant2)
		self.session.commit()

		self.admin = muesli.models.User()
		self.admin.first_name = u'Anton'
		self.admin.last_name = u'Admin'
		self.admin.email = 'admin@muesli.org'
		self.admin.is_admin = 1
		setUserPassword(self.admin, 'adminpassword')
		self.session.add(self.admin)
		self.session.commit()

		self.lecture = muesli.models.Lecture()
		self.lecture.name = "Irgendwas"
		self.lecture.assistant = self.assistant
		self.session.add(self.lecture)
		self.lecture.tutors.append(self.tutor)
		self.session.commit()

		self.lecture2 = muesli.models.Lecture()
		self.lecture2.name = "Irgendwas2"
		self.lecture2.assistant = self.assistant2
		self.session.add(self.lecture2)
		self.session.commit()

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user.id, status=403)

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=403)

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/list', status=200)
		self.assertTrue('Irgendwas' in res.body)
		self.assertTrue('Assistent' in res.body)

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=403)

	def test_lecture_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % self.lecture.id, status=403)

	def test_lecture_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % self.lecture.id, status=403)

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)
	def setUser(self, user):
		self.testapp.post('/user/login',{'email': user.email, 'password': user.realpassword}, status=302)
	def tearDown(self):
		UnloggedTests.tearDown(self)

	def test_start(self):
		# Now we are logged in, thus we should
		# get 200 instead of 302
		res = self.testapp.get('/start', status=200)

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user.id, status=200)

	def test_user2_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user2.id, status=403)

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=200)

class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user.id, status=403)

	def test_user2_edit(self):
		pass

class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)

	def test_lecture_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % self.lecture.id, status=200)

	def test_lecture2_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % self.lecture2.id, status=403)

class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user.id, status=200)

	def test_admin(self):
		res = self.testapp.get('/admin', status=200)

	def test_user_list(self):
		res = self.testapp.get('/user/list', status=200)

	def test_lecture2_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % self.lecture2.id, status=200)
