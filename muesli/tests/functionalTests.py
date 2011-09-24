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
	#def __init__(self, *args, **kwargs):
		#unittest.TestCase.__init__(self, *args, **kwargs)
		#urls = ['/user/login',
			#'/lecture/list']
		#for url in urls:
			#name = url.replace('/', '_')
			#setattr(self, name, lambda: self.testapp.get(url, status=200))

	def test_user_login(self):
		res = self.testapp.get('/user/login', status=200)
	
	def test_lecture_view(self):
		res = self.testapp.get('/lecture/list', status=200)

	#def test_start(self):
		#res = self.testapp.get('/start', status=200)


	#def test_zzz(self):
		##session = muesli.models.Session()
		###print "Anzahl lectures", session.query(muesli.models.Lecture).count()
		#res = self.testapp.get('/lecture/list', status=200)

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
	
	def test_lecture_view(self):
		res = self.testapp.get('/lecture/list', status=200)
		self.assertTrue('Irgendwas' in res.body)
		self.assertTrue('Nachname' in res.body)