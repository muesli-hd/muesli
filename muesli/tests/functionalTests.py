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

from hashlib import sha1

import unittest
import muesli.web
import muesli.types
import muesli.mail
from muesli import utils

from sqlalchemy.orm import relationship, sessionmaker

class OrigDatabaseTests(unittest.TestCase):
    def setUp(self):
        import muesli.web
        from muesli.web import main
        app = main({}, testmode=True)
        from webtest import TestApp
        self.testapp = TestApp(app)

    def test_root(self):
        #session = muesli.models.Session()
        #print("Anzahl lectures", session.query(muesli.models.Lecture).count())
        res = self.testapp.get('/lecture/list', status=200)
        self.assertTrue('Liste' in res)

    def test_login(self):
        res = self.testapp.get('/user/login', status=200)
        self.assertTrue(True)

class BaseTests(unittest.TestCase):
    def setUp(self):
        import muesli
        import sqlalchemy
        self.config = muesli.config

        databaseName = muesli.config['database']['connection']
        databaseName = databaseName + "test"
        self.engine = sqlalchemy.create_engine(databaseName)

        import muesli.models
        muesli.models.Base.metadata.create_all(self.engine)
        muesli.mailerName = 'pyramid_mailer.testing'
        muesli.mail.testing=True
        muesli.old_engine = muesli.engine
        muesli.engine = lambda: self.engine
        import muesli.web
        from muesli.web import main
        self.app = main({})
        from webtest import TestApp
        self.testapp = TestApp(self.app)
        self.session = muesli.models.Session()
        for table in reversed(muesli.models.Base.metadata.sorted_tables):
            self.session.execute(table.delete())
        self.session.commit()

        self.populate()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()
        muesli.engine = muesli.old_engine

    def populate(self):
        pass

    def assertResContains(self, res, content):
        self.assertTrue(content in res)

    def assertResContainsNot(self, res, content):
        self.assertTrue(content not in res)

    def assertForm(self, res, name, newvalue, formindex=None, expectedvalue=None):
        def getForm(res):
            if formindex != None:
                return res.forms[formindex]
            else:
                return res.form
        form = getForm(res)
        form[name] = newvalue
        res2 = form.submit()
        self.assertResContainsNot(res2, 'formerror')
        form = getForm(res2)
        if expectedvalue==None: expectedvalue=newvalue
        self.assertTrue(form[name].value == expectedvalue)
        return res2

def setUserPassword(user, password):
    user.realpassword = password
    user.password = sha1(password.encode('utf-8')).hexdigest()

class PopulatedTests(BaseTests):
    def populate(self):
        self.user = muesli.models.User()
        self.user.first_name = 'Stefan'
        self.user.last_name = 'Student'
        self.user.email = 'user@muesli.org'
        self.user.subject = self.config['subjects'][0]
        setUserPassword(self.user, 'userpassword')
        self.session.add(self.user)
        #self.session.commit()

        self.user2 = muesli.models.User()
        self.user2.first_name = 'Sigmund'
        self.user2.last_name = 'Student'
        self.user2.email = 'user2@muesli.org'
        self.user2.subject = self.config['subjects'][1]
        setUserPassword(self.user2, 'user2password')
        self.session.add(self.user2)

        self.user_without_lecture = muesli.models.User()
        self.user_without_lecture.first_name = 'Sebastian'
        self.user_without_lecture.last_name = 'Student'
        self.user_without_lecture.email = 'user_without_lecture@muesli.org'
        self.user_without_lecture.subject = self.config['subjects'][1]
        setUserPassword(self.user_without_lecture, 'user_without_lecturepassword')
        self.session.add(self.user_without_lecture)

        self.user_unconfirmed = muesli.models.User()
        self.user_unconfirmed.first_name = 'Ulrich'
        self.user_unconfirmed.last_name = 'Student'
        self.user_unconfirmed.email = 'user_unconfirmed@muesli.org'
        confirmation = muesli.models.Confirmation()
        confirmation.user = self.user_unconfirmed
        confirmation.source = 'user/register'
        self.session.add(self.user_unconfirmed)
        self.session.add(confirmation)

        self.unicodeuser = muesli.models.User()
        self.unicodeuser.first_name = 'Uli'
        self.unicodeuser.last_name = 'Unicode'
        self.unicodeuser.email = 'unicodeuser@muesli.org'
        self.unicodeuser.subject = self.config['subjects'][1]
        setUserPassword(self.unicodeuser, 'üüü')
        self.session.add(self.unicodeuser)
        #self.session.commit()

        self.tutor = muesli.models.User()
        self.tutor.first_name = 'Thorsten'
        self.tutor.last_name = 'Tutor'
        self.tutor.email = 'tutor@muesli.org'
        self.tutor.subject = self.config['subjects'][2]
        setUserPassword(self.tutor, 'tutorpassword')
        self.session.add(self.tutor)
        #self.session.commit()

        self.tutor2 = muesli.models.User()
        self.tutor2.first_name = 'Thor2sten'
        self.tutor2.last_name = 'Tu2tor'
        self.tutor2.email = 'tutor2@muesli.org'
        self.tutor2.subject = self.config['subjects'][0]
        setUserPassword(self.tutor2, 'tutor2password')
        self.session.add(self.tutor2)
        #self.session.commit()

        self.assistant = muesli.models.User()
        self.assistant.first_name = 'Armin'
        self.assistant.last_name = 'Assistent'
        self.assistant.email = 'assistant@muesli.org'
        self.assistant.subject = self.config['subjects'][0]
        setUserPassword(self.assistant, 'assistantpassword')
        self.assistant.is_assistant=1
        self.session.add(self.assistant)
        #self.session.commit()

        self.assistant2 = muesli.models.User()
        self.assistant2.first_name = 'Armin'
        self.assistant2.last_name = 'Assistent2'
        self.assistant2.email = 'assistant2@muesli.org'
        self.assistant2.subject = self.config['subjects'][0]
        setUserPassword(self.assistant2, 'assistant2password')
        self.assistant2.is_assistant=1
        self.session.add(self.assistant2)
        #self.session.commit()

        self.admin = muesli.models.User()
        self.admin.first_name = 'Anton'
        self.admin.last_name = 'Admin'
        self.admin.email = 'admin@muesli.org'
        self.admin.subject = self.config['subjects'][0]
        self.admin.is_admin = 1
        setUserPassword(self.admin, 'adminpassword')
        self.session.add(self.admin)
        #self.session.commit()

        self.lecture = muesli.models.Lecture()
        self.lecture.name = "Irgendwas"
        self.lecture.mode = 'direct'
        self.lecture.password = 'geheim'
        self.lecture.assistants.append(self.assistant)
        self.lecture.tutor_rights = utils.editOwnTutorials
        self.session.add(self.lecture)
        self.lecture.tutors.append(self.tutor2)
        self.lecture.tutors.append(self.tutor)
        #self.session.commit()

        self.exam = muesli.models.Exam()
        self.exam.name = "Aufgabenblatt 1"
        self.exam.lecture = self.lecture
        self.exam.category = utils.categories[0]['id']
        self.admission = True
        self.registration = True
        self.session.add(self.exam)
        self.exercise = muesli.models.Exercise()
        self.exercise.nr = 1
        self.exercise.maxpoints = 4
        self.exercise.exam = self.exam
        self.session.add(self.exercise)

        self.exam2 = muesli.models.Exam()
        self.exam2.name = "Aufgabenblatt 2"
        self.exam2.lecture = self.lecture
        self.exam2.category = utils.categories[0]['id']
        self.session.add(self.exam2)
        #self.session.commit()

        self.lecture2 = muesli.models.Lecture()
        self.lecture2.name = "Irgendwas2"
        self.lecture2.assistants.append(self.assistant2)
        self.session.add(self.lecture2)

        tutorial = muesli.models.Tutorial()
        tutorial.lecture = self.lecture2
        tutorial.tutor = self.tutor
        tutorial.place = 'In einer weiter entfernten Galaxis'
        tutorial.max_students = 42
        tutorial.time = muesli.types.TutorialTime('0 14:00')
        self.lecture2_tutorial = tutorial
        self.session.add(self.lecture2_tutorial)
        #self.session.commit()

        self.tutorial = muesli.models.Tutorial()
        self.tutorial.lecture = self.lecture
        self.tutorial.tutor = self.tutor
        self.tutorial.place = 'In einer weit entfernten Galaxis'
        self.tutorial.max_students = 42
        self.tutorial.time = muesli.types.TutorialTime('0 12:00')
        self.session.add(self.tutorial)

        tutorial = muesli.models.Tutorial()
        tutorial.lecture = self.lecture
        tutorial.tutor = self.tutor2
        tutorial.place = 'In einer noch weiter entfernten Galaxis'
        tutorial.max_students = 42
        tutorial.time = muesli.types.TutorialTime('0 16:00')
        self.tutorial_tutor2 = tutorial
        self.session.add(self.tutorial_tutor2)

        tutorial = muesli.models.Tutorial()
        tutorial.lecture = self.lecture
        tutorial.place = 'In einer noch viel weiter entfernten Galaxis'
        tutorial.max_students = 42
        tutorial.time = muesli.types.TutorialTime('0 18:00')
        self.tutorial_no_tutor= tutorial
        self.session.add(self.tutorial_no_tutor)

        self.lecture_student = muesli.models.LectureStudent()
        self.lecture_student.student = self.user
        self.lecture_student.lecture = self.lecture
        self.lecture_student.tutorial = self.tutorial
        self.session.add(self.lecture_student)

        #self.session.commit()

        self.tutorial2 = muesli.models.Tutorial()
        self.tutorial2.lecture = self.lecture
        self.tutorial2.tutor = self.tutor
        self.tutorial2.place = 'In einer weit entfernten Galaxis'
        self.tutorial2.max_students = 42
        self.tutorial2.time = muesli.types.TutorialTime('0 14:00')
        self.session.add(self.tutorial2)

        self.lecture_student2 = muesli.models.LectureStudent()
        self.lecture_student2.student = self.user2
        self.lecture_student2.lecture = self.lecture
        self.lecture_student2.tutorial = self.tutorial2
        self.session.add(self.lecture_student2)

        self.grading = muesli.models.Grading()
        self.grading.name = 'Endnote'
        self.grading.lecture = self.lecture
        self.grading.exams.append(self.exam)
        self.session.add(self.grading)

        self.prefLecture = muesli.models.Lecture()
        self.prefLecture.name = "Vorlieben"
        self.prefLecture.mode = 'prefs'
        self.prefLecture.assistants.append(self.assistant)
        self.session.add(self.prefLecture)

        self.prefTutorial = muesli.models.Tutorial()
        self.prefTutorial.lecture = self.prefLecture
        self.prefTutorial.tutor = self.tutor2
        self.prefTutorial.place = 'In einer weit entfernten Galaxis'
        self.prefTutorial.max_students = 42
        self.prefTutorial.time = muesli.types.TutorialTime('0 14:00')
        self.session.add(self.prefTutorial)

        self.prefTutorial2 = muesli.models.Tutorial()
        self.prefTutorial2.lecture = self.prefLecture
        self.prefTutorial2.tutor = self.tutor2
        self.prefTutorial2.place = 'In einer weiter entfernten Galaxis'
        self.prefTutorial2.max_students = 42
        self.prefTutorial2.time = muesli.types.TutorialTime('0 16:00')
        self.session.add(self.prefTutorial2)

        self.timePreference = muesli.models.TimePreference(self.prefLecture, self.user, self.prefTutorial.time, 1)
        self.session.add(self.timePreference)

        self.session.commit()

    def setUser(self, user):
        self.loggedUser = user
        res = self.testapp.get('/user/login', status=200)
        res.form['email'] = user.email
        res.form['password'] = user.realpassword
        res = res.form.submit()
        self.assertEqual(res.status_int, 302)
        #res = self.testapp.post('/user/login',{'email': user.email, 'password': user.realpassword}, status=302)

class UserLoggedInTests(PopulatedTests):
    def setUp(self):
        PopulatedTests.setUp(self)
        self.setUser(self.user)

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

class UnicodeUserTests(PopulatedTests):
    def setUp(self):
        PopulatedTests.setUp(self)
        self.setUser(self.unicodeuser)
