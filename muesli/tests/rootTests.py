# -*- coding: utf-8 -*-
#
# muesli/tests/rootTests.py
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
	def test_start(self):
		res = self.testapp.get('/start', status=302)

	def test_admin(self):
		res = self.testapp.get('/admin', status=403)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
	pass

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)

	def test_start(self):
		# Now we are logged in, thus we should
		# get 200 instead of 302
		res = self.testapp.get('/start', status=200)

class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)

class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)


class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)

	def test_admin(self):
		res = self.testapp.get('/admin', status=200)