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
	def test_grading_edit(self):
		res = self.testapp.get('/grading/edit/%s' % 12345, status=404)

	def test_grading_associate_exam(self):
		res = self.testapp.get('/grading/associate_exam/%s' % 12345, status=404)

	def test_grading_delete_exam_association(self):
		res = self.testapp.get('/grading/delete_exam_association/%s/%s' % (12345,12), status=404)

	def test_grading_enter_grades(self):
		res = self.testapp.get('/grading/enter_grades/%s' % 12345, status=404)


class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
	def test_grading_edit(self):
		res = self.testapp.get('/grading/edit/%s' % self.grading.id, status=403)

	def test_grading_associate_exam(self):
		res = self.testapp.get('/grading/associate_exam/%s' % self.grading.id, status=403)

	def test_grading_delete_exam_association(self):
		res = self.testapp.get('/grading/delete_exam_association/%s/%s' % (self.grading.id, self.exam.id), status=403)

	def test_grading_enter_grades(self):
		res = self.testapp.get('/grading/enter_grades/%s' % self.grading.id, status=403)

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)


class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)


class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)

	def test_grading_edit(self):
		res = self.testapp.get('/grading/edit/%s' % self.grading.id, status=200)

	def test_grading_associate_exam(self):
		self.assertTrue(self.exam2 not in self.grading.exams)
		res = self.testapp.post('/grading/associate_exam/%s' % self.grading.id, {'new_exam': self.exam2.id}, status=302)
		self.session.expire_all()
		self.assertTrue(self.exam2 in self.grading.exams)

	def test_grading_delete_exam_association(self):
		self.assertTrue(self.exam in self.grading.exams)
		res = self.testapp.get('/grading/delete_exam_association/%s/%s' % (self.grading.id, self.exam.id), status=302)
		self.session.expire_all()
		self.assertTrue(self.exam not in self.grading.exams)

	def test_grading_enter_grades(self):
		res = self.testapp.get('/grading/enter_grades/%s' % self.grading.id, status=200)
		# Caution: Need format 'x.y', otherwise test will fail
		self.testForm(res, 'grade-%i' % self.user.id, '2.0', formindex=2)


class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)
