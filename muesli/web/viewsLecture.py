# -*- coding: utf-8 -*-
#
# muesli/web/viewsLecture.py
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

from muesli import models
from muesli import utils
from muesli.web.context import *
from muesli.web.forms import *

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound
from pyramid.url import route_url
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message, Attachment

from sqlalchemy.orm import exc
import sqlalchemy

import re
import os

@view_config(route_name='lecture_list', renderer='muesli.web:templates/lecture/list.pt')
class List(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
	def __call__(self):
		lectures = self.db.query(models.Lecture).order_by(models.Lecture.term)
		if self.request.GET.get('show_all', '0')=='0':
			lectures = lectures.filter(models.Lecture.is_visible == True)
		return {'lectures': lectures.all()}

@view_config(route_name='lecture_view', renderer='muesli.web:templates/lecture/view.pt', context=LectureContext, permission='view')
class View(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		times = lecture.prepareTimePreferences(user=self.request.user)
		return {'lecture': lecture,
		        'times': times,
		        'prefs': utils.preferences}

@view_config(route_name='lecture_add_exam', renderer='muesli.web:templates/lecture/add_exam.pt', context=LectureContext, permission='edit')
class AddExam(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		form = LectureAddExam(self.request)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			exam = models.Exam()
			exam.lecture = lecture
			form.obj = exam
			form.saveValues()
			self.request.db.commit()
			form.message = "Neues Testat angelegt."
		return {'lecture': lecture,
		        'form': form
		       }

@view_config(route_name='lecture_add_grading', renderer='muesli.web:templates/lecture/add_grading.pt', context=LectureContext, permission='edit')
class AddGrading(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		form = LectureAddGrading(self.request)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			grading = models.Grading()
			grading.lecture = lecture
			form.obj = grading
			form.saveValues()
			self.request.db.commit()
			form.message = "Neue Benotung angelegt."
		return {'lecture': lecture,
		        'form': form
		       }

@view_config(route_name='lecture_edit', renderer='muesli.web:templates/lecture/edit.pt', context=LectureContext, permission='edit')
class Edit(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		form = LectureEdit(self.request, lecture)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			form.saveValues()
			self.request.db.commit()
		names = utils.lecture_types[lecture.type]
		pref_subjects = lecture.pref_subjects()
		pref_count = sum([pref[0] for pref in pref_subjects])
		subjects = lecture.subjects()
		student_count = sum([subj[0] for subj in subjects])
		return {'lecture': lecture,
		        'names': names,
		        'pref_subjects': pref_subjects,
		        'pref_count': pref_count,
		        'subjects': subjects,
		        'student_count': student_count,
		        'categories': utils.categories,
		        'exams': dict([[cat['id'], lecture.exams.filter(models.Exam.category==cat['id'])] for cat in utils.categories]),
		        'form': form}

@view_config(route_name='lecture_remove_tutor', context=LectureContext, permission='edit')
class RemoveTutor(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
		self.tutor_id = request.matchdict['tutor_id']
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		tutor = self.db.query(models.User).get(self.tutor_id)
		if not tutor:
			return
		if not tutor in lecture.tutors:
			return
		lecture.tutors.remove(tutor)
		self.db.commit()
		return HTTPFound(location=self.request.route_url('lecture_edit', lecture_id=lecture.id))

@view_config(route_name='lecture_export_students_html', renderer='muesli.web:templates/lecture/export_students_html.pt', context=LectureContext, permission='edit')
class ExportStudentsHtml(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		students = lecture.lecture_students_for_tutorials([])
		if 'subject' in self.request.GET:
			students = students.filter(models.LectureStudent.student.has(models.User.subject==self.request.GET['subject']))
		return {'lecture': lecture,
		        'lecture_students': students}

@view_config(route_name='lecture_email_tutors', renderer='muesli.web:templates/lecture/email_tutors.pt', context=LectureContext, permission='edit')
def emailTutors(request):
	db = request.db
	lecture = request.context.lecture
	form = LectureEmailTutors()
	if request.method == 'POST' and form.processPostData(request.POST):
		tutors = lecture.tutors
		mailer = get_mailer(request)
		message = Message(subject=form['subject'],
			sender=request.user.email,
			recipients= [lecture.assistant.email],
			# Due to a bug, bcc does not work in pyramid_mailer at the moment.
			# Thus the email will be sent to the assistent only
			bcc=[t.email for t in tutors],
			body=form['body'])
		if request.POST['attachments'] not in ['', None]:
			a = Attachment(request.POST['attachments'].filename, data=request.POST['attachments'].file)
			message.attach(a)
		# As we are not using transactions,
		# we send the mail immediately.
		mailer.send_immediately(message)
		request.session.flash('A Mail has been send to all tutors of this lecture', queue='messages')
	return {'lecture': lecture,
	        'form': form}

@view_config(route_name='lecture_email_students', renderer='muesli.web:templates/lecture/email_students.pt', context=LectureContext, permission='edit')
def emailStudents(request):
	db = request.db
	lecture = request.context.lecture
	form = LectureEmailTutors()
	if request.method == 'POST' and form.processPostData(request.POST):
		students = lecture.students
		mailer = get_mailer(request)
		message = Message(subject=form['subject'],
			sender=request.user.email,
			recipients= [lecture.assistant.email],
			# Due to a bug, bcc does not work in pyramid_mailer at the moment.
			# Thus the email will be sent to the assistent only
			bcc=[s.email for s in students],
			body=form['body'])
		if request.POST['attachments'] not in ['', None]:
			a = Attachment(request.POST['attachments'].filename, data=request.POST['attachments'].file)
			message.attach(a)
		# As we are not using transactions,
		# we send the mail immediately.
		mailer.send_immediately(message)
		request.session.flash('A Mail has been send to all tutors of this lecture', queue='messages')
	return {'lecture': lecture,
	        'form': form}