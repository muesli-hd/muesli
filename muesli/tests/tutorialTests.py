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

class BaseTests(functionalTests.BaseTests):
	def test_tutorial_view(self):
		res = self.testapp.get('/tutorial/view/%s' % 12456, status=403)

	def test_tutorial_occupancy_bar(self):
		res = self.testapp.get('/tutorial/occupancy_bar/10/20/30', status=200)
		self.assertTrue(res.content_type=='image/png')

	def test_tutorial_add(self):
		res = self.testapp.get('/tutorial/add/%s' % 12456, status=404)

	def test_tutorial_edit(self):
		res = self.testapp.get('/tutorial/edit/%s' % 12456, status=403)

	def test_tutorial_results(self):
		res = self.testapp.get('/tutorial/results/%s' % 12456, status=403)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
	def test_tutorial_view(self):
		res = self.testapp.get('/tutorial/view/%s' % self.tutorial.id, status=403)

	def test_tutorial_add(self):
		res = self.testapp.get('/tutorial/add/%s' % self.lecture.id, status=403)

	def test_tutorial_edit(self):
		res = self.testapp.get('/tutorial/edit/%s' % self.tutorial.id, status=403)

	def test_tutorial_results(self):
		res = self.testapp.get('/tutorial/results/%s' % self.tutorial.id, status=403)

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)

class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)

	def test_tutorial_view(self):
		res = self.testapp.get('/tutorial/view/%s' % self.tutorial.id, status=200)

	def test_tutorial_results(self):
		res = self.testapp.get('/tutorial/results/%s' % self.tutorial.id, status=200)
		res = self.testapp.get('/tutorial/results/%s,%s' % (self.tutorial.id, self.tutorial2.id), status=200)


class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)

	def test_tutorial_add(self):
		res = self.testapp.get('/tutorial/add/%s' % self.lecture.id, status=200)

	def test_tutorial_edit(self):
		res = self.testapp.get('/tutorial/edit/%s' % self.tutorial.id, status=200)

class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)
