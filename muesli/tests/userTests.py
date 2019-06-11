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
import datetime

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

    def test_user_check(self):
        res = self.testapp.get('/user/check', status=403)

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
        form['matrikel'] = 'ui123'
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

    def test_user_register_other(self):
        res = self.testapp.get('/user/register_other', status=200)
        form = res.form
        form['email'] = 'matthias@matthias-k.org'
        form['first_name'] = 'Matthias'
        res = form.submit()
        self.assertTrue(res.status.startswith('200'))
        self.assertResContains(res, 'formerror')
        form = res.form
        form['email'] = 'matthias@matthias-k.org'
        form['first_name'] = 'Matthias'
        form['last_name'] = 'Kümmerer'
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

    def test_user_change_email(self):
        res = self.testapp.get('/user/change_email', status=403)

    def test_user_change_password(self):
        res = self.testapp.get('/user/change_password', status=403)

    def test_user_reset_password(self):
        res = self.testapp.get('/user/reset_password', status=200)
        res.form['email'] = 'does-not-exist@muesli.org'
        res = res.form.submit()
        self.assertTrue(res.status.startswith('200'))

    def test_user_reset_password2(self):
        res = self.testapp.get('/user/reset_password2', status=200)

    def test_user_ajax_complete(self):
        res = self.testapp.get('/user/ajax_complete/%s/%s' % (123,234), status=403)

    def test_user_delete(self):
        res = self.testapp.get('/user/delete/%s' % (1234), status=404)

    def test_user_delete_unconfirmed(self):
        res = self.testapp.get('/user/delete_unconfirmed', status=403)

    def test_user_doublets(self):
        res = self.testapp.get('/user/doublets', status=403)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
    def test_user_edit(self):
        res = self.testapp.get('/user/edit/%s' % self.user.id, status=403)

    def test_user_reset_password(self):
        res = self.testapp.get('/user/reset_password', status=200)
        res.form['email'] = self.user.email
        res = res.form.submit()
        self.assertTrue(res.status.startswith('302'))

    def test_user_reset_password(self):
        res = self.testapp.get('/user/reset_password', status=200)
        res.form['email'] = self.user.email
        res = res.form.submit()
        self.assertTrue(res.status.startswith('302'))

    def test_user_reset_password3(self):
        self.test_user_reset_password()
        self.session.expire_all()
        confirmation = self.session.query(Confirmation).filter(Confirmation.user_id == self.user.id).one()
        user = confirmation.user
        res = self.testapp.get('/user/reset_password3/%s' % confirmation.hash, status=200)
        res.form['password'] = 'testpasswort'
        res.form['password_repeat'] = 'testpasswort'
        res = res.form.submit()
        self.assertTrue(res.status.startswith('302'))
        self.assertResContainsNot(res, 'formerror')
        user.realpassword = 'testpasswort'
        res = self.testapp.get('/user/logout', status=302)
        self.setUser(user)

    def test_user_ajax_complete(self):
        res = self.testapp.get('/user/ajax_complete/%s/%s' % (self.lecture.id,self.tutorial.id), status=403)

    def test_user_register_same_email(self):
        res = self.testapp.get('/user/register', status=200)
        form = res.form
        # Same email
        form['email'] = self.user.email
        form['first_name'] = 'Matthias'
        form['last_name'] = 'Kümmerer'
        form['subject'] = 'Mathematik (Dipl.)'
        form['matrikel'] = '1234567'
        form['birth_date'] = '01.12.1999'
        form['birth_place'] = 'Hintertupfingen'
        res = form.submit()
        self.assertTrue(res.status.startswith('200'))
        self.assertResContains(res, 'existiert bereits')
        form = res.form
        # Same email different cases
        form['email'] = self.user.email.upper()
        form['first_name'] = 'Matthias'
        form['last_name'] = 'Kümmerer'
        form['subject'] = 'Mathematik (Dipl.)'
        form['matrikel'] = '1234567'
        form['birth_date'] = '01.12.1999'
        form['birth_place'] = 'Hintertupfingen'
        res = form.submit()
        self.assertTrue(res.status.startswith('200'))
        self.assertResContains(res, 'existiert bereits')

    def test_user_delete(self):
        res = self.testapp.get('/user/delete/%s' % (self.user2.id), status=403)

class UnicodeTests(functionalTests.UnicodeUserTests):
    def test_unicodepassword(self):
        res = self.testapp.get('/start', status=200)

class UserLoggedInTests(UnloggedTests):
    def setUp(self):
        UnloggedTests.setUp(self)
        self.setUser(self.user)

    def test_user_edit(self):
        res = self.testapp.get('/user/edit/%s' % self.user.id, status=403)

    def test_user_update(self):
        res = self.testapp.get('/user/update', status=200)
        self.assertForm(res, 'matrikel', '2613945')

    def test_user_check(self):
        res = self.testapp.get('/user/check', status=200)

    def test_user_change_email(self):
        res = self.testapp.get('/user/change_email', status=200)
        res.form['email'] = 'test@muesli.org'
        res = res.form.submit()
        self.assertTrue(res.status.startswith('302'))

    def test_user_confirm_email(self):
        self.test_user_change_email()
        self.session.expire_all()
        self.assertEqual(len(self.loggedUser.confirmations), 1)
        confirmation = self.loggedUser.confirmations[0]
        newmail = confirmation.what
        user = confirmation.user
        res = self.testapp.get('/user/confirm_email/%s' % confirmation.hash, status=200)
        res = res.form.submit('abort')
        self.session.expire_all()
        self.assertTrue(confirmation not in user.confirmations)
        self.assertTrue(user.email != newmail)

        self.test_user_change_email()
        self.session.expire_all()
        self.assertEqual(len(self.loggedUser.confirmations), 1)
        confirmation = self.loggedUser.confirmations[0]
        user = confirmation.user
        res = self.testapp.get('/user/confirm_email/%s' % confirmation.hash, status=200)
        res = res.form.submit('confirm')
        self.session.expire_all()
        self.assertTrue(confirmation not in user.confirmations)
        self.assertTrue(user.email == newmail)
        #form['password'] = 'test'
        #form['password_repeat'] = 'test'
        #res = form.submit()
        #self.session.expire_all()
        #self.assertTrue(res.status.startswith('302'))
        #self.assertTrue(confirmation not in user.confirmations)
        #self.assertTrue(user.password != None)

    def test_user_change_password(self):
        res = self.testapp.get('/user/change_password', status=200)
        res.form['old_password'] = self.loggedUser.realpassword
        res.form['new_password'] = 'testpasswort'
        res.form['new_password_repeat'] = 'testpasswort'
        res = res.form.submit()
        self.assertTrue(res.status.startswith('200'))
        self.assertResContainsNot(res, 'formerror')
        self.loggedUser.realpassword = 'testpasswort'
        res = self.testapp.get('/user/logout', status=302)
        self.setUser(self.loggedUser)

class TutorLoggedInTests(UserLoggedInTests):
    def setUp(self):
        UserLoggedInTests.setUp(self)
        self.setUser(self.tutor)

    def test_user_ajax_complete_tut(self):
        res = self.testapp.post('/user/ajax_complete/%s/%s' % (self.lecture.id,self.tutorial.id),
               {'name': 'GarantiertKeinName'}, status=200)
        self.assertResContainsNot(res, '</li>')
        res = self.testapp.post('/user/ajax_complete/%s/%s' % (self.lecture.id,self.tutorial.id),
               {'name': self.tutorial.students[0].last_name}, status=200)
        self.assertResContains(res, self.tutorial.students[0].first_name)

    def test_user_ajax_complete(self):
        #All tutors should be allowed to see students from all
        #tutorials
        res = self.testapp.post('/user/ajax_complete/%s/' % (self.lecture.id),
               {'name': 'GarantiertKeinName'}, status=200)
        self.assertResContainsNot(res, '</li>')
        res = self.testapp.post('/user/ajax_complete/%s/' % (self.lecture.id,),
               {'name': self.tutorial.students[0].last_name}, status=200)
        self.assertResContains(res, self.tutorial.students[0].first_name)

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
        self.user.subject='Ein süßer Umlaut'
        self.session.commit()
        res = self.testapp.get('/user/edit/%s' % self.user.id, status=200)

    def test_user_list(self):
        res = self.testapp.get('/user/list', status=200)

    def test_user_delete(self):
        #Do not delete students from tutorials
        res = self.testapp.get('/user/delete/%s' % (self.user2.id), status=302)
        self.assertIn('/user/edit/%s' % self.user2.id, res.headers['location'])
        res = res.follow()
        self.assertResContains(res, 'Tutorien angemeldet')
        self.assertResContainsNot(res, 'wurde gelöscht')

        #Do not delete tutors
        res = self.testapp.get('/user/delete/%s' % (self.tutor.id), status=302)
        self.assertIn('/user/edit/%s' % self.tutor.id, res.headers['location'])
        res = res.follow()
        self.assertResContains(res, 'Tutor von Tutorien')
        self.assertResContainsNot(res, 'wurde gelöscht')

        # Do not delete assistants
        res = self.testapp.get('/user/delete/%s' % (self.assistant.id), status=302)
        self.assertIn('/user/edit/%s' % self.assistant.id, res.headers['location'])
        res = res.follow()
        self.assertResContains(res, 'verwaltet Vorlesungen')
        self.assertResContainsNot(res, 'wurde gelöscht')

        # Do not delete students who have points in Müsli
        e = ExerciseStudent()
        e.student = self.user_without_lecture
        e.exercise = self.exercise
        self.session.add(e)
        self.session.commit()
        res = self.testapp.get('/user/delete/%s' % (self.user_without_lecture.id), status=302)
        self.assertIn('/user/edit/%s' % self.user_without_lecture.id, res.headers['location'])
        res = res.follow()
        self.assertResContains(res, 'eingetragene Punkte')
        self.assertResContainsNot(res, 'wurde gelöscht')
        self.session.delete(e)
        self.session.commit()

        # Do not delete Students who have grades in Müsli
        e = StudentGrade()
        e.student = self.user_without_lecture
        e.grading = self.grading
        self.session.add(e)
        self.session.commit()
        res = self.testapp.get('/user/delete/%s' % (self.user_without_lecture.id), status=302)
        self.assertIn('/user/edit/%s' % self.user_without_lecture.id, res.headers['location'])
        res = res.follow()
        self.assertResContains(res, 'eingetragene Noten')
        self.assertResContainsNot(res, 'wurde gelöscht')
        self.session.delete(e)
        self.session.commit()

        res = self.testapp.get('/user/delete/%s' % (self.user_unconfirmed.id), status=302)
        self.assertIn('/admin', res.headers['location'])
        res = res.follow()
        self.assertResContains(res, 'wurde gelöscht')

        res = self.testapp.get('/user/delete/%s' % (self.user_without_lecture.id), status=302)
        self.assertIn('/admin', res.headers['location'])
        res = res.follow()
        self.assertResContains(res, 'wurde gelöscht')

    def test_user_delete_unconfirmed(self):
        student_count = self.session.query(muesli.models.User).count()
        res = self.testapp.get('/user/delete_unconfirmed', status=200)
        res = res.form.submit()
        self.assertEqual(res.status_int, 200)
        # Do not delete students with too new confirmations
        self.assertResContains(res, '0 Studenten gelöscht')
        self.session.expire_all()
        self.assertEqual(self.session.query(muesli.models.User).count(), student_count)
        # But do delete students with old confirmations
        self.user_unconfirmed.confirmations[0].created_on -= datetime.timedelta(60)
        self.session.commit()
        res = self.testapp.get('/user/delete_unconfirmed', status=200)
        res = res.form.submit()
        self.assertEqual(res.status_int, 200)
        self.assertResContains(res, '1 Studenten gelöscht')
        self.session.expire_all()
        self.assertEqual(self.session.query(muesli.models.User).count(), student_count-1)

    def test_user_doublets(self):
        res = self.testapp.get('/user/doublets', status=200)
