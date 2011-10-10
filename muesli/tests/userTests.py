# -*- coding: utf-8 -*-
#
# muesli/tests/userTests.py
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
from muesli.tests import functionalTests
from muesli.models import *

class BaseTests(functionalTests.BaseTests):
	def test_user_login(self):
		res = self.testapp.get('/user/login', status=200)
	
	def test_user_logout(self):
		res = self.testapp.get('/user/logout', status=302)

	def test_user_list(self):
		res = self.testapp.get('/user/list', status=403)

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % 1234, status=404)

	def test_user_update(self):
		res = self.testapp.get('/user/update', status=403)

	def test_user_register(self):
		res = self.testapp.get('/user/register', status=200)
		form = res.form
		form['email'] = 'matthias@matthias-k.org'
		form['first_name'] = 'Matthias'
		form['subject'] = 'Mathematik (Dipl.)'
		form['matrikel'] = '1234567'
		form['birth_date'] = '01.12.1999'
		form['birth_place'] = 'Hintertupfingen'
		res = form.submit()
		self.assertTrue(res.status.startswith('200'))
		self.assertResContains(res, 'formerror')
		form = res.form
		form['email'] = 'matthias@matthias-k.org'
		form['first_name'] = 'Matthias'
		form['last_name'] = 'Kümmerer'
		form['subject'] = 'Mathematik (Dipl.)'
		form['matrikel'] = '1234567'
		form['birth_date'] = '01.12.1999'
		form['birth_place'] = 'Hintertupfingen'
		res = form.submit()
		self.assertTrue(res.status.startswith('302'))

	def test_user_confirm(self):
		self.test_user_register()
		self.session.expire_all()
		user = self.session.query(User).filter(User.email=='matthias@matthias-k.org').one()
		confirmation = user.confirmations[0]
		res = self.testapp.get('/user/confirm/%s' % confirmation.hash, status=200)
		form =  res.form
		form['password'] = 'test'
		form['password_repeat'] = 'test'
		res = form.submit()
		self.session.expire_all()
		self.assertTrue(res.status.startswith('302'))
		self.assertTrue(confirmation not in user.confirmations)
		self.assertTrue(user.password != None)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user.id, status=403)

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user.id, status=200)

	def test_user2_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user2.id, status=403)

	def test_user_update(self):
		res = self.testapp.get('/user/update', status=200)
		self.assertForm(res, 'matrikel', '2613945')


class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)

	def test_user_edit(self):
		pass

	def test_user2_edit(self):
		pass

class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)


class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)

	def test_user_edit(self):
		res = self.testapp.get('/user/edit/%s' % self.user.id, status=200)
		self.assertForm(res, 'first_name', 'Neuer Vorname')
		res = self.testapp.get('/user/edit/%s' % self.tutor.id, status=200)
		res = self.testapp.get('/user/edit/%s' % self.assistant.id, status=200)
		res = self.testapp.get('/user/edit/%s' % self.admin.id, status=200)

	def test_user_list(self):
		res = self.testapp.get('/user/list', status=200)