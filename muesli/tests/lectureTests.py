# -*- coding: utf-8 -*-
#
# muesli/tests/lectureTests.py
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
	def test_lecture_list(self):
		res = self.testapp.get('/lecture/list', status=200)

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/view/%s' % 12456, status=404)

	def test_lecture_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % 123456, status=404)

	def test_lecture_add_exam(self):
		res = self.testapp.get('/lecture/add_exam/%s' % 123456, status=404)

	def test_lecture_add_grading(self):
		res = self.testapp.get('/lecture/add_grading/%s' % 123456, status=404)

	def test_lecture_remove_tutor(self):
		res = self.testapp.get('/lecture/remove_tutor/%s/%s' % (123456,123), status=404)

	def test_lecture_export_students_html(self):
		res = self.testapp.get('/lecture/export_students_html/%s' % 123456, status=404)

	def test_lecture_email_tutors(self):
		res = self.testapp.get('/lecture/email_tutors/%s' % 123456, status=404)

	def test_lecture_email_students(self):
		res = self.testapp.get('/lecture/email_students/%s' % 123456, status=404)

	def test_lecture_view_removed_students(self):
		res = self.testapp.get('/lecture/view_removed_students/%s' % 12456, status=404)

	def test_lecture_export_totals(self):
		res = self.testapp.get('/lecture/export_totals/%s' % 123456, status=404)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
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

	def test_lecture_add_exam(self):
		res = self.testapp.get('/lecture/add_exam/%s' % self.lecture.id, status=403)

	def test_lecture_add_grading(self):
		res = self.testapp.get('/lecture/add_grading/%s' % self.lecture.id, status=403)

	def test_lecture_remove_tutor(self):
		res = self.testapp.get('/lecture/remove_tutor/%s/%s' % (self.lecture.id,self.tutor.id), status=403)

	def test_lecture_export_students_html(self):
		res = self.testapp.get('/lecture/export_students_html/%s' % self.lecture.id, status=403)

	def test_lecture_email_tutors(self):
		res = self.testapp.get('/lecture/email_tutors/%s' % self.lecture.id, status=403)

	def test_lecture_email_students(self):
		res = self.testapp.get('/lecture/email_students/%s' % self.lecture.id, status=403)

	def test_lecture_view_removed_students(self):
		res = self.testapp.get('/lecture/view_removed_students/%s' % self.lecture.id, status=403)

	def test_lecture_export_totals(self):
		res = self.testapp.get('/lecture/export_totals/%s' % self.lecture.id, status=403)


class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)

	def test_lecture_view(self):
		res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=200)

class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)

class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)

	def test_lecture_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % self.lecture.id, status=200)
		self.assertForm(res, 'name', 'Irgendwie anders')

	def test_lecture2_edit(self):
		res = self.testapp.get('/lecture/edit/%s' % self.lecture2.id, status=403)

	def test_lecture_add_exam(self):
		res = self.testapp.get('/lecture/add_exam/%s' % self.lecture.id, status=200)

	def test_lecture_add_grading(self):
		res = self.testapp.get('/lecture/add_grading/%s' % self.lecture.id, status=200)

	def test_lecture_remove_tutor(self):
		self.assertTrue(self.tutor2 in self.lecture.tutors)
		res = self.testapp.get('/lecture/remove_tutor/%s/%s' % (self.lecture.id,self.tutor2.id), status=302)
		self.session.expire_all()
		self.assertTrue(self.tutor2 not in self.lecture.tutors)

	def test_lecture_export_students_html(self):
		res = self.testapp.get('/lecture/export_students_html/%s' % self.lecture.id, status=200)

	def test_lecture_email_tutors(self):
		res = self.testapp.get('/lecture/email_tutors/%s' % self.lecture.id, status=200)

	def test_lecture_email_students(self):
		res = self.testapp.get('/lecture/email_students/%s' % self.lecture.id, status=200)

	def test_lecture_view_removed_students(self):
		res = self.testapp.get('/lecture/view_removed_students/%s' % self.lecture.id, status=200)

	def test_lecture_export_totals(self):
		res = self.testapp.get('/lecture/export_totals/%s' % self.lecture.id, status=200)


class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)

	def test_lecture2_edit(self):
		pass
