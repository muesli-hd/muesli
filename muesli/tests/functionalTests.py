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
from muesli import utils

from sqlalchemy.orm import relationship, sessionmaker

class OrigDatabaseTests(unittest.TestCase):
	def setUp(self):
		import muesli.web
		from muesli.web import main
		app = main({})
		from webtest import TestApp
		self.testapp = TestApp(app)

	def test_root(self):
		#session = muesli.models.Session()
		#print "Anzahl lectures", session.query(muesli.models.Lecture).count()
		res = self.testapp.get('/lecture/list', status=200)
		self.failUnless('Liste' in res.body)
	
	def test_login(self):
		res = self.testapp.get('/user/login', status=200)
		self.failUnless(True)

class BaseTests(unittest.TestCase):
	def setUp(self):
		import muesli
		import sqlalchemy
		self.engine = sqlalchemy.create_engine('postgresql:///mueslitest')

		import muesli.models
		muesli.models.Base.metadata.create_all(self.engine)
		muesli.mailerName = 'pyramid_mailer.testing'
		muesli.old_engine = muesli.engine
		muesli.engine = lambda: self.engine
		import muesli.web
		from muesli.web import main
		app = main({})
		from webtest import TestApp
		self.testapp = TestApp(app)
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
		self.assertTrue(content.encode(res.charset) in res.body)

	def assertResContainsNot(self, res, content):
		self.assertTrue(content.encode(res.charset) not in res.body)

	def assertForm(self, res, name, newvalue, formindex=None):
		def getForm(res):
			if formindex != None:
				return res.forms[formindex]
			else:
				return res.form
		form = getForm(res)
		form[name] = newvalue
		res2 = form.submit()
		self.assertResContainsNot(res2, u'formerror')
		form = getForm(res2)
		self.assertTrue(form[name].value == newvalue)
		return res2

def setUserPassword(user, password):
	user.realpassword = password
	user.password = sha1(password).hexdigest()

class PopulatedTests(BaseTests):
	def populate(self):
		self.user = muesli.models.User()
		self.user.first_name = u'Stefan'
		self.user.last_name = u'Student'
		self.user.email = 'user@muesli.org'
		self.user.subject = utils.subjects[0]
		setUserPassword(self.user, 'userpassword')
		self.session.add(self.user)
		#self.session.commit()

		self.user2 = muesli.models.User()
		self.user2.first_name = u'Sigmund'
		self.user2.last_name = u'Student'
		self.user2.email = 'user2@muesli.org'
		self.user2.subject = utils.subjects[1]
		setUserPassword(self.user2, 'user2password')
		self.session.add(self.user2)
		#self.session.commit()

		self.tutor = muesli.models.User()
		self.tutor.first_name = u'Thorsten'
		self.tutor.last_name = u'Tutor'
		self.tutor.email = 'tutor@muesli.org'
		self.tutor.subject = utils.subjects[2]
		setUserPassword(self.tutor, 'tutorpassword')
		self.session.add(self.tutor)
		#self.session.commit()

		self.tutor2 = muesli.models.User()
		self.tutor2.first_name = u'Thor2sten'
		self.tutor2.last_name = u'Tu2tor'
		self.tutor2.email = 'tutor2@muesli.org'
		self.tutor2.subject = utils.subjects[0]
		setUserPassword(self.tutor2, 'tutor2password')
		self.session.add(self.tutor2)
		#self.session.commit()

		self.assistant = muesli.models.User()
		self.assistant.first_name = u'Armin'
		self.assistant.last_name = u'Assistent'
		self.assistant.email = 'assistant@muesli.org'
		self.assistant.subject = utils.subjects[0]
		setUserPassword(self.assistant, 'assistantpassword')
		self.assistant.is_assistant=1
		self.session.add(self.assistant)
		#self.session.commit()

		self.assistant2 = muesli.models.User()
		self.assistant2.first_name = u'Armin'
		self.assistant2.last_name = u'Assistent2'
		self.assistant2.email = 'assistant2@muesli.org'
		self.assistant2.subject = utils.subjects[0]
		setUserPassword(self.assistant2, 'assistant2password')
		self.assistant2.is_assistant=1
		self.session.add(self.assistant2)
		#self.session.commit()

		self.admin = muesli.models.User()
		self.admin.first_name = u'Anton'
		self.admin.last_name = u'Admin'
		self.admin.email = 'admin@muesli.org'
		self.admin.subject = utils.subjects[0]
		self.admin.is_admin = 1
		setUserPassword(self.admin, 'adminpassword')
		self.session.add(self.admin)
		#self.session.commit()

		self.lecture = muesli.models.Lecture()
		self.lecture.name = "Irgendwas"
		self.lecture.assistant = self.assistant
		self.session.add(self.lecture)
		self.lecture.tutors.append(self.tutor2)
		self.lecture.tutors.append(self.tutor)
		#self.session.commit()

		self.exam = muesli.models.Exam()
		self.exam.name = u"Aufgabenblatt 1"
		self.exam.lecture = self.lecture
		self.exam.category = utils.categories[0]['id']
		self.session.add(self.exam)
		self.exercise = muesli.models.Exercise()
		self.exercise.nr = 1
		self.exercise.maxpoints = 4
		self.exercise.exam = self.exam
		self.session.add(self.exercise)

		self.exam2 = muesli.models.Exam()
		self.exam2.name = u"Aufgabenblatt 2"
		self.exam2.lecture = self.lecture
		self.exam2.category = utils.categories[0]['id']
		self.session.add(self.exam2)
		#self.session.commit()

		self.lecture2 = muesli.models.Lecture()
		self.lecture2.name = "Irgendwas2"
		self.lecture2.assistant = self.assistant2
		self.session.add(self.lecture2)
		#self.session.commit()

		self.tutorial = muesli.models.Tutorial()
		self.tutorial.lecture = self.lecture
		self.tutorial.tutor = self.tutor
		self.tutorial.place = 'In einer weit entfernten Galaxis'
		self.tutorial.max_students = 42
		self.tutorial.time = muesli.types.TutorialTime('0 12:00')
		self.session.add(self.tutorial)

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
		self.prefLecture.assistant = self.assistant
		self.session.add(self.prefLecture)

		self.prefTutorial = muesli.models.Tutorial()
		self.prefTutorial.lecture = self.lecture
		self.prefTutorial.tutor = self.tutor2
		self.prefTutorial.place = 'In einer weit entfernten Galaxis'
		self.prefTutorial.max_students = 42
		self.prefTutorial.time = muesli.types.TutorialTime('0 14:00')
		self.session.add(self.prefTutorial)

		self.timePreference = muesli.models.TimePreference(self.prefLecture, self.user, self.prefTutorial.time, 1)
		self.session.add(self.timePreference)

		self.session.commit()

	def setUser(self, user):
		self.testapp.post('/user/login',{'email': user.email, 'password': user.realpassword}, status=302)

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


