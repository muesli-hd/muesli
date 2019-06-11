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
        self.assertResContainsNot(res, '/lecture/add')

    def test_lecture_view(self):
        res = self.testapp.get('/lecture/view/%s' % 12456, status=404)

    def test_lecture_add(self):
        res = self.testapp.get('/lecture/add', status=403)

    def test_lecture_edit(self):
        res = self.testapp.get('/lecture/edit/%s' % 123456, status=404)

    def test_lecture_do_allocation(self):
        res = self.testapp.get('/lecture/do_allocation/%s' % 123456, status=404)

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

    def test_lecture_set_preferences(self):
        res = self.testapp.get('/lecture/set_preferences/%s' % 123456, status=404)

    def test_lecture_remove_preferences(self):
        res = self.testapp.get('/lecture/remove_preferences/%s' % 123456, status=404)

    def test_lecture_view_points(self):
        res = self.testapp.get('/lecture/view_points/%s' % 123456, status=404)

    def test_lecture_add_tutor(self):
        res = self.testapp.get('/lecture/add_tutor/%s' % 123456, status=404)

    def test_lecture_change_assistants(self):
        res = self.testapp.get('/lecture/change_assistants/%s' % 123456, status=404)

    def test_lecture_add_student(self):
        res = self.testapp.get('/lecture/add_student/%s' % 123456, status=404)

    def test_lecture_switch_students(self):
        res = self.testapp.get('/lecture/switch_students/%s' % 123456, status=404)

    def test_lecture_export_yaml(self):
        res = self.testapp.get('/lecture/export_yaml', status=403)

    def test_all_lecture_export_excel(self):
        res = self.testapp.get('/lecture/export_excel/downloadDetailTutorials.xlsx', status=403)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
    def test_lecture_view(self):
        res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=403)

    def test_lecture_view(self):
        res = self.testapp.get('/lecture/list', status=200)
        self.assertTrue('Irgendwas' in res)
        self.assertTrue('Assistent' in res)

    def test_lecture_view(self):
        res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=403)

    def test_lecture_edit(self):
        res = self.testapp.get('/lecture/edit/%s' % self.lecture.id, status=403)

    def test_lecture_do_allocation(self):
        res = self.testapp.get('/lecture/do_allocation/%s' % self.prefLecture.id, status=403)

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

    def test_lecture_set_preferences(self):
        res = self.testapp.get('/lecture/set_preferences/%s' % self.prefLecture.id, status=403)

    def test_lecture_remove_preferences(self):
        res = self.testapp.get('/lecture/remove_preferences/%s' % self.prefLecture.id, status=403)

    def test_lecture_view_points(self):
        res = self.testapp.get('/lecture/view_points/%s' % self.lecture.id, status=403)

    def test_lecture_add_tutor(self):
        res = self.testapp.get('/lecture/add_tutor/%s' % self.lecture.id, status=403)

    def test_lecture_change_assistants(self):
        res = self.testapp.get('/lecture/change_assistants/%s' % self.lecture.id, status=403)

    def test_lecture_add_student(self):
        res = self.testapp.get('/lecture/add_student/%s' % self.lecture.id, status=403)

    def test_lecture_switch_students(self):
        res = self.testapp.get('/lecture/switch_students/%s' % self.lecture.id, status=403)

    def test_all_lecture_export_excel(self):
        res = self.testapp.get('/lecture/export_excel/downloadDetailTutorials.xlsx', status=403)

class UserLoggedInTests(UnloggedTests):
    def setUp(self):
        UnloggedTests.setUp(self)
        self.setUser(self.user)

    def test_lecture_view(self):
        res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=200)
        self.assertResContainsNot(res, 'bernehmen')

    def test_lecture_set_preferences(self):
        prefcount = len(self.loggedUser.time_preferences)
        res = self.testapp.get('/lecture/set_preferences/%s' % self.prefLecture.id, status=302)
        res = self.testapp.get('/lecture/view/%s' % self.prefLecture.id, status=200)
        form = res.forms[0]
        #Works only, if there are no tutorials with same time!
        for i,tut in enumerate(self.prefLecture.tutorials):
            form['time-%s' % (i+1)] = str(tut.time)
            form['pref-%s'% (i+1)] = "1"
        res = form.submit()
        self.assertTrue(res.status.startswith('302'))
        res = res.follow()
        self.session.expire_all()
        self.assertGreater(len(self.loggedUser.time_preferences), prefcount)

    def test_lecture_remove_preferences(self):
        res = self.testapp.get('/lecture/remove_preferences/%s' % self.prefLecture.id, status=302)
        self.assertTrue(len(self.loggedUser.time_preferences) == 0)

    def test_lecture_view_points(self):
        res = self.testapp.get('/lecture/view_points/%s' % self.lecture.id, status=200)

    def test_lecture_add_tutor(self):
        alreadyTutor = self.loggedUser in self.lecture.tutors
        res = self.testapp.post('/lecture/add_tutor/%s' % self.lecture.id, {'password': ''}, status=302)
        res = res.follow()
        res.mustcontain('Fehler aufgetreten')
        res = self.testapp.post('/lecture/add_tutor/%s' % self.lecture.id, {'password': self.lecture.password}, status=302)
        res = res.follow()
        if alreadyTutor:
            res.mustcontain('Sie sind bereits')
        else:
            res.mustcontain('Sie wurden als')

    def test_all_lecture_export_excel(self):
        res = self.testapp.get('/lecture/export_excel/downloadDetailTutorials.xlsx', status=403)

class TutorLoggedInTests(UserLoggedInTests):
    def setUp(self):
        UserLoggedInTests.setUp(self)
        self.setUser(self.tutor)

    def test_lecture_view(self):
        res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=200)
        self.assertResContains(res, 'bernehmen')

    def test_lecture_view_points(self):
        res = self.testapp.get('/lecture/view_points/%s' % self.lecture.id, status=403)

    def test_lecture_email_tutors(self):
        res = self.testapp.get('/lecture/email_tutors/%s' % self.lecture.id, status=200)

    def test_all_lecture_export_excel(self):
        res = self.testapp.get('/lecture/export_excel/downloadDetailTutorials.xlsx', status=403)


class AssistantLoggedInTests(TutorLoggedInTests):
    def setUp(self):
        TutorLoggedInTests.setUp(self)
        self.setUser(self.assistant)

    def test_lecture_list(self):
        res = self.testapp.get('/lecture/list', status=200)
        self.assertResContains(res, '/lecture/add')

    def test_lecture_view(self):
        res = self.testapp.get('/lecture/view/%s' % self.lecture.id, status=200)

    def test_lecture_add(self):
        res = self.testapp.get('/lecture/add', status=200)
        leccount = self.session.query(muesli.models.Lecture).count()
        res.form['name'] = 'Testvorlesung'
        res = res.form.submit()
        self.assertTrue(res.status.startswith('302'))
        self.session.expire_all()
        leccount2 = self.session.query(muesli.models.Lecture).count()
        self.assertEqual(leccount+1, leccount2)

    def test_lecture_edit(self):
        res = self.testapp.get('/lecture/edit/%s' % self.lecture.id, status=200)
        self.assertForm(res, 'name', 'Irgendwie anders', formindex=0)

    def test_lecture2_edit(self):
        res = self.testapp.get('/lecture/edit/%s' % self.lecture2.id, status=403)

    def test_lecture_change_assistants(self):
        res = self.testapp.get('/lecture/change_assistants/%s' % self.lecture.id, status=302)

    def test_lecture_do_allocation(self):
        res = self.testapp.get('/lecture/do_allocation/%s' % self.prefLecture.id, status=200)
        self.session.expire_all()
        self.assertGreater(self.prefLecture.lecture_students.count(), 0)
        for ls in self.prefLecture.lecture_students.all():
            self.assertEqual(ls.tutorial.lecture_id, self.prefLecture.id)
        res = res.forms[0].submit()
        self.assertTrue(res.status.startswith('302'))
        self.session.expire_all()
        self.assertEqual(self.prefLecture.lecture_students.count(), 0)
        # Should be catched:
        res = self.testapp.get('/lecture/do_allocation/%s' % self.lecture.id, status=403)

    def test_lecture_add_exam(self):
        res = self.testapp.get('/lecture/add_exam/%s' % self.lecture.id, status=200)
        form =  res.form
        form['name'] = 'Testblatt'
        res = form.submit()
        self.assertEqual(res.status_int, 302)

    def test_lecture_add_grading(self):
        res = self.testapp.get('/lecture/add_grading/%s' % self.lecture.id, status=200)

    def test_lecture_remove_tutor(self):
        self.assertTrue(self.tutor2 in self.lecture.tutors)
        res = self.testapp.get('/lecture/remove_tutor/%s/%s' % (self.lecture.id,self.tutor2.id), status=302)
        self.session.expire_all()
        self.assertTrue(self.tutor2 not in self.lecture.tutors)

    def test_lecture_export_students_html(self):
        res = self.testapp.get('/lecture/export_students_html/%s' % self.lecture.id, status=200)

    def test_lecture_email_students(self):
        res = self.testapp.get('/lecture/email_students/%s' % self.lecture.id, status=200)

    def test_lecture_view_removed_students(self):
        res = self.testapp.get('/lecture/view_removed_students/%s' % self.lecture.id, status=200)

    def test_lecture_export_totals(self):
        res = self.testapp.get('/lecture/export_totals/%s' % self.lecture.id, status=200)

    def test_lecture_switch_students(self):
        res = self.testapp.get('/lecture/switch_students/%s' % self.lecture.id, status=200)

    def test_lecture_add_student(self):
        self.assertNotIn(self.user_without_lecture, self.lecture.students)
        res = self.testapp.get('/lecture/add_student/%s' % self.lecture.id, status=200)
        form = res.form
        form['student_email'] = self.user_without_lecture.email
        form['new_tutorial']  = self.lecture.tutorials[0].id
        res = form.submit()
        self.assertTrue(res.status.startswith('200'))
        self.session.expire_all()
        self.assertIn(self.user_without_lecture, self.lecture.students)
        self.assertIn(self.user_without_lecture, self.lecture.tutorials[0].students)

    def test_lecture_add_student_removed(self):
        res = self.testapp.get('/tutorial/remove_student/%s/%s' % (self.tutorial.id, self.user.id), status=302)
        res = self.testapp.get('/lecture/add_student/%s' % self.lecture.id, status=200)
        form = res.form
        form['student_email'] = self.user.email
        form['new_tutorial']  = self.lecture.tutorials[0].id
        res = form.submit()
        self.assertTrue(res.status.startswith('200'))
        self.session.expire_all()
        self.assertIn(self.user, self.lecture.students)
        self.assertIn(self.user, self.lecture.tutorials[0].students)

    def test_lecture_add_student_exists(self):
        res = self.testapp.get('/lecture/add_student/%s' % self.lecture.id, status=200)
        form = res.form
        form['student_email'] = self.user.email
        form['new_tutorial']  = self.lecture.tutorials[0].id
        res = form.submit()
        self.assertResContains(res, 'bereits eingetragen')


class AdminLoggedInTests(AssistantLoggedInTests):
    def setUp(self):
        AssistantLoggedInTests.setUp(self)
        self.setUser(self.admin)

    def test_lecture2_edit(self):
        pass

    def test_lecture_export_yaml(self):
        res = self.testapp.get('/lecture/export_yaml', status=200)
        self.assertEqual(res.content_type, 'application/x-yaml')

    def test_all_lecture_export_excel(self):
        res = self.testapp.get('/lecture/export_excel/downloadDetailTutorials.xlsx', status=200)
        self.assertEqual(res.content_type, 'application/vnd.ms-excel')
