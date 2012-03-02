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
import json

class BaseTests(functionalTests.BaseTests):
	def test_exam_edit(self):
		res = self.testapp.get('/exam/edit/%s' % 12345, status=404)

	def test_exam_add_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/' % 12345, status=404)

	def test_exam_edit_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/%s' % (12345, 23456), status=404)

	def test_exam_enter_points(self):
		res = self.testapp.get('/exam/enter_points/%s/' % 12345, status=404)

	def test_exam_statistics(self):
		res = self.testapp.get('/exam/statistics/%s/' % 12345, status=404)

	def test_exam_histogram_for_exercise(self):
		res = self.testapp.get('/exam/histogram_for_exercise/%s/' % 12345, status=404)

	def test_exam_histogram_for_exam(self):
		res = self.testapp.get('/exam/histogram_for_exam/%s/' % 12345, status=404)

	def test_exam_enter_points_tuts(self):
		res = self.testapp.get('/exam/enter_points/%s/%s' % (12345, '12,23'), status=404)

	def test_exam_admission(self):
		res = self.testapp.get('/exam/admission/%s/' % 12345, status=404)

	def test_exam_admission_tuts(self):
		res = self.testapp.get('/exam/admission/%s/%s' % (12345, '12,23'), status=404)

	def test_exam_export(self):
		res = self.testapp.get('/exam/export/%s/' % 12345, status=404)

	def test_exam_export_tuts(self):
		res = self.testapp.get('/exam/export/%s/%s,%s' % (12345, 12,23), status=404)

	def test_exam_ajax_save_points(self):
		res = self.testapp.get('/exam/ajax_save_points/%s/%s,%s' % (12345, 12,23), status=404)

	def test_exam_ajax_get_points(self):
		res = self.testapp.get('/exam/ajax_get_points/%s/%s,%s' % (12345, 12,23), status=404)


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

	def test_exam_statistics(self):
		res = self.testapp.get('/exam/statistics/%s/' % self.exam.id, status=403)
		res = self.testapp.get('/exam/statistics/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=403)

	def test_exam_histogram_for_exercise(self):
		res = self.testapp.get('/exam/histogram_for_exercise/%s/' % self.exercise.id, status=403)
		res = self.testapp.get('/exam/histogram_for_exercise/%s/%s,%s' % (self.exercise.id, self.tutorial.id, self.tutorial2.id), status=403)

	def test_exam_histogram_for_exam(self):
		res = self.testapp.get('/exam/histogram_for_exam/%s/' % self.exam.id, status=403)
		res = self.testapp.get('/exam/histogram_for_exam/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=403)

	def test_exam_export(self):
		res = self.testapp.get('/exam/export/%s/' % self.exam.id, status=403)

	def test_exam_export_tuts(self):
		res = self.testapp.get('/exam/export/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), status=403)

	def test_exam_admission(self):
		res = self.testapp.get('/exam/admission/%s/' % self.exam.id, status=403)

	def test_exam_admission_tuts(self):
		res = self.testapp.get('/exam/admission/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=403)

	def test_exam_ajax_save_points(self):
		res = self.testapp.get('/exam/ajax_save_points/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), status=403)

	def test_exam_ajax_get_points(self):
		res = self.testapp.get('/exam/ajax_get_points/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), status=403)

class UserLoggedInTests(UnloggedTests):
	def setUp(self):
		UnloggedTests.setUp(self)
		self.setUser(self.user)


class TutorLoggedInTests(UserLoggedInTests):
	def setUp(self):
		UserLoggedInTests.setUp(self)
		self.setUser(self.tutor)

	#def test_exam_enter_points(self):
		#test later if this can be allowed for tutors.
		#res = self.testapp.get('/exam/enter_points/%s/' % self.exam.id, status=200)
		#self.assertForm(res, 'points-%s-%s' % (self.user.id, self.exercise.id), '1.5', formindex=0)
		#self.assertForm(res, 'points-%s-%s' % (self.user2.id, self.exercise.id), '3.5', formindex=0)

	def test_exam_enter_points_tuts(self):
		res = self.testapp.get('/exam/enter_points/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=200)
		self.assertForm(res, 'points-%s-%s' % (self.user.id, self.exercise.id), '1.5', formindex=0)
		self.assertForm(res, 'points-%s-%s' % (self.user2.id, self.exercise.id), '3.5', formindex=0)
		res = self.testapp.get('/exam/enter_points/%s/%s' % (self.exam.id, self.tutorial.id), status=200)
		self.assertForm(res, 'points-%s-%s' % (self.user.id, self.exercise.id), '2.5', formindex=0)
		self.assertResContainsNot(res, 'points-%s-%s' % (self.user2.id, self.exercise.id))

	def test_exam_admission(self):
		res = self.testapp.get('/exam/admission/%s/' % self.exam.id, status=403)

	def test_exam_admission_tuts(self):
		res = self.testapp.get('/exam/admission/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=200)

	def test_exam_statistics(self):
		res = self.testapp.get('/exam/statistics/%s/' % self.exam.id, status=200)
		res = self.testapp.get('/exam/statistics/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=200)

	def test_exam_histogram_for_exercise(self):
		res = self.testapp.get('/exam/histogram_for_exercise/%s/' % self.exercise.id, status=200)
		res = self.testapp.get('/exam/histogram_for_exercise/%s/%s,%s' % (self.exercise.id, self.tutorial.id, self.tutorial2.id), status=200)

	def test_exam_histogram_for_exam(self):
		res = self.testapp.get('/exam/histogram_for_exam/%s/' % self.exam.id, status=200)
		res = self.testapp.get('/exam/histogram_for_exam/%s/%s,%s' % (self.exam.id, self.tutorial.id, self.tutorial2.id), status=200)

	#def test_exam_export(self):
		#Test later
		#res = self.testapp.get('/exam/export/%s/' % self.exam.id, status=200)

	def test_exam_export_tuts(self):
		res = self.testapp.get('/exam/export/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), status=200)

	def test_exam_ajax_save_points(self):
		post = {'student_id': self.user.id}
		post['points-%s' % self.exercise.id] = 3.0
		self.assertTrue(len(self.user.exercise_points)==0)
		res = self.testapp.post('/exam/ajax_save_points/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), post,status=200)
		self.assertTrue(res.status.startswith('200'))
		self.session.expire_all()
		self.assertTrue(len(self.user.exercise_points)>0)

	def test_exam_ajax_get_points(self):
		post = {'student_id': self.user.id}
		res = self.testapp.post('/exam/ajax_get_points/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), post, status=200)
		self.assertTrue(res.status.startswith('200'))
		data = json.loads(res.body)
		self.assertTrue(len(data['points'])==0)
		self.test_exam_ajax_save_points()
		res = self.testapp.post('/exam/ajax_get_points/%s/%s,%s' % (self.exam.id, self.tutorial.id,self.tutorial2.id), post, status=200)
		self.assertTrue(res.status.startswith('200'))
		data = json.loads(res.body)
		self.assertTrue(len(data['points'])==1)
		self.assertTrue(data['points']['%s' % self.exercise.id]==3)

class AssistantLoggedInTests(TutorLoggedInTests):
	def setUp(self):
		TutorLoggedInTests.setUp(self)
		self.setUser(self.assistant)

	def test_exam_enter_points(self):
		res = self.testapp.get('/exam/enter_points/%s/' % self.exam.id, status=200)
		self.assertForm(res, 'points-%s-%s' % (self.user.id, self.exercise.id), '1.5', formindex=0)
		self.assertForm(res, 'points-%s-%s' % (self.user2.id, self.exercise.id), '3.5', formindex=0)

	def test_exam_admission(self):
		self.exam.admission=True
		self.exam.registration=False
		self.session.commit()
		res = self.testapp.get('/exam/admission/%s/' % self.exam.id, status=200)
		self.assertForm(res, 'admission-%s' % (self.user.id), '1', formindex=0)
		self.assertForm(res, 'admission-%s' % (self.user.id), '0', formindex=0)
		self.assertForm(res, 'admission-%s' % (self.user.id), '', formindex=0)
		self.assertForm(res, 'registration-%s' % (self.user.id), '1', expectedvalue='')
		self.assertForm(res, 'registration-%s' % (self.user.id), '0', expectedvalue='')
		self.assertForm(res, 'registration-%s' % (self.user.id), '', expectedvalue='')
		self.exam.admission=False
		self.exam.registration=True
		self.session.commit()
		res = self.testapp.get('/exam/admission/%s/' % self.exam.id, status=200)
		self.assertForm(res, 'admission-%s' % (self.user.id), '1', expectedvalue='')
		self.assertForm(res, 'admission-%s' % (self.user.id), '0', expectedvalue='')
		self.assertForm(res, 'admission-%s' % (self.user.id), '', expectedvalue='')
		self.assertForm(res, 'registration-%s' % (self.user.id), '1')
		self.assertForm(res, 'registration-%s' % (self.user.id), '0')
		self.assertForm(res, 'registration-%s' % (self.user.id), '')

	def test_exam_edit(self):
		res = self.testapp.get('/exam/edit/%s' % self.exam.id, status=200)
		self.assertForm(res, 'name', 'Neuer Name')

	def test_exam_add_exercise(self):
		self.assertTrue(len(self.exam.exercises)==1)
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/' % self.exam.id, status=200)
		res.form['nr'] = '2'
		res.form['maxpoints'] = 4
		res = res.form.submit()
		self.session.expire_all()
		self.assertTrue(len(self.exam.exercises)==2)

	def test_exam_edit_exercise(self):
		res = self.testapp.get('/exam/add_or_edit_exercise/%s/%s' % (self.exam.id, self.exercise.id), status=200)
		self.assertForm(res, 'maxpoints', '5')

	def test_exam_export(self):
		res = self.testapp.get('/exam/export/%s/' % self.exam.id, status=200)

class AdminLoggedInTests(AssistantLoggedInTests):
	def setUp(self):
		AssistantLoggedInTests.setUp(self)
		self.setUser(self.admin)
