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

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/list', status=200)

def setUserPassword(user, password):
	user.realpassword = password
	user.password = sha1(password).hexdigest()

class UnloggedTests(BaseTests):
	def populate(self):
		self.assistant = muesli.models.User()
		self.assistant.first_name = u'Vorname'
		self.assistant.last_name = u'Nachname'
		self.assistant.email = 'assistant@muesli.org'
		self.assistant.is_assistant=True
		self.session.add(self.assistant)
		self.session.commit()
		self.lecture = muesli.models.Lecture()
		self.lecture.name = "Irgendwas"
		self.lecture.assistant = self.assistant
		self.session.add(self.lecture)
		self.session.commit()
		self.user = muesli.models.User()
		self.user.first_name = u'Stefan'
		self.user.last_name = u'Student'
		self.user.email = 'user@muesli.org'
		setUserPassword(self.user, 'userpassword')
		self.session.add(self.user)
		self.session.commit()
		self.admin = muesli.models.User()
		self.admin.first_name = u'Anton'
		self.admin.last_name = u'Admin'
		self.admin.email = 'admin@muesli.org'
		self.admin.is_admin = 1
		setUserPassword(self.admin, 'adminpassword')
		self.session.add(self.admin)
		self.session.commit()
	
	def test_lecture_view(self):
		res = self.testapp.get('/lecture/list', status=200)
		self.assertTrue('Irgendwas' in res.body)
		self.assertTrue('Nachname' in res.body)

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)
	def setUser(self, user):
		self.testapp.post('/user/login',{'email': user.email, 'password': user.realpassword}, status=302)
	def tearDown(self):
		#pyramid.security.authenticated_userid = pyramid.security.authenticated_userid_old
		UnloggedTests.tearDown(self)

	def test_start(self):
		# Now we are logged in, thus we should
		# get 200 instead of 302
		res = self.testapp.get('/start', status=200)

class AdminLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.admin)

	def test_admin(self):
		res = self.testapp.get('/admin', status=200)

	def test_user_list(self):
		res = self.testapp.get('/user/list', status=200)
