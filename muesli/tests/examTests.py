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
	def test_exam_edit(self):
		res = self.testapp.get('/exam/edit/%s' % 12345, status=404)

	def test_exam_add_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/' % 12345, status=404)

	def test_exam_edit_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/%s' % (12345, 23456), status=404)

	def test_exam_enter_points(self):
		res = self.testapp.get('/exam/enter_points/%s/' % 12345, status=404)

	def test_exam_enter_points_tuts(self):
		res = self.testapp.get('/exam/enter_points/%s/%s' % (12345, '12,23'), status=404)

	def test_exam_export(self):
		res = self.testapp.get('/exam/export/%s/' % 12345, status=404)

	def test_exam_export_tuts(self):
		res = self.testapp.get('/exam/export/%s/%s,%s' % (12345, 12,23), status=404)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
	def test_exam_edit(self):
		res = self.testapp.get('/exam/edit/%s' % self.exam.id, status=403)

	def test_exam_add_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/' % self.exam.id, status=403)

	def test_exam_edit_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/%s' % (self.exam.id, self.exercise.id), status=403)

	def test_exam_enter_points(self):
		res = self.testapp.get('/exam/enter_points/%s/' % self.exam.id, status=403)

	def test_exam_enter_points_tuts(self):
		res = self.testapp.get('/exam/enter_points/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=403)

	def test_exam_export(self):
		res = self.testapp.get('/exam/export/%s/' % self.exam.id, status=403)

	def test_exam_export_tuts(self):
		res = self.testapp.get('/exam/export/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), status=403)

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)


class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)

	def test_exam_enter_points(self):
		res = self.testapp.get('/exam/enter_points/%s/' % self.exam.id, status=200)
		self.testForm(res, 'points-%s-%s' % (self.user.id, self.exercise.id), '1.5', formindex=0)
		self.testForm(res, 'points-%s-%s' % (self.user2.id, self.exercise.id), '3.5', formindex=0)


	def test_exam_enter_points_tuts(self):
		res = self.testapp.get('/exam/enter_points/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=200)
		self.testForm(res, 'points-%s-%s' % (self.user.id, self.exercise.id), '1.5', formindex=0)
		self.testForm(res, 'points-%s-%s' % (self.user2.id, self.exercise.id), '3.5', formindex=0)
		res = self.testapp.get('/exam/enter_points/%s/%s' % (self.exam.id, self.tutorial.id), status=200)
		self.testForm(res, 'points-%s-%s' % (self.user.id, self.exercise.id), '2.5', formindex=0)
		self.assertResContainsNot(res, 'points-%s-%s' % (self.user2.id, self.exercise.id))

	def test_exam_export(self):
		res = self.testapp.get('/exam/export/%s/' % self.exam.id, status=200)

	def test_exam_export_tuts(self):
		res = self.testapp.get('/exam/export/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), status=200)


class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)

	def test_exam_edit(self):
		res = self.testapp.get('/exam/edit/%s' % self.exam.id, status=200)
		self.testForm(res, 'name', 'Neuer Name')

	def test_exam_add_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/' % self.exam.id, status=200)

	def test_exam_edit_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/%s' % (self.exam.id, self.exercise.id), status=200)
		self.testForm(res, 'maxpoints', '5')


class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)
