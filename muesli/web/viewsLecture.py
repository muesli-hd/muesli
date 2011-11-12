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
from muesli.allocation import Allocation
from muesli.mail import Message, sendMail


from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound, HTTPForbidden
from pyramid.url import route_url

from sqlalchemy.orm import exc, joinedload
import sqlalchemy

from muesli import types

import re
import os

@view_config(route_name='lecture_list', renderer='muesli.web:templates/lecture/list.pt')
class List(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
	def __call__(self):
		lectures = self.db.query(models.Lecture).order_by(models.Lecture.term).joinedload(models.Lecture.assistant)
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
		message = Message(subject=form['subject'],
			sender=request.user.email,
			to= [lecture.assistant.email],
			bcc=[t.email for t in tutors],
			body=form['body'])
		if request.POST['attachments'] not in ['', None]:
			message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
		sendMail(message)
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
		message = Message(subject=form['subject'],
			sender=request.user.email,
			to= [lecture.assistant.email],
			bcc=[s.email for s in students],
			body=form['body'])
		if request.POST['attachments'] not in ['', None]:
			message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
		sendMail(message)
		request.session.flash('A Mail has been send to all tutors of this lecture', queue='messages')
	return {'lecture': lecture,
	        'form': form}

@view_config(route_name='lecture_view_removed_students', renderer='muesli.web:templates/lecture/view_removed_students.pt', context=LectureContext, permission='edit')
def viewRemovedStudents(request):
	db = request.db
	lecture = request.context.lecture
	ls = lecture.lecture_removed_students
	ls = ls.join(LectureRemovedStudent.student).order_by(User.last_name, User.first_name)
	return {'lecture': lecture,
	        'removed_students': ls}

@view_config(route_name='lecture_export_totals', renderer='muesli.web:templates/lecture/export_totals.pt', context=LectureContext, permission='edit')
def exportTotals(request):
	db = request.db
	lecture = request.context.lecture
	# TODO: Order by tutor/student
	ls = lecture.lecture_students_for_tutorials(order=False)
	Tutor = sqlalchemy.orm.aliased(models.User)
	ls = ls.join(models.LectureStudent.student).join(models.LectureStudent.tutorial).join(Tutor, models.Tutorial.tutor).order_by(Tutor.last_name, models.User.last_name, models.User.first_name)
	lecture_results = lecture.getLectureResults(students=ls)
	results = DictOfObjects(lambda: DictOfObjects(lambda: {}))
	for res in lecture_results:
		results[res.student_id]['results'][res.Exam.id] = res.points
	cat_results = lecture.getLectureResultsByCategory(students=ls)
	for res in cat_results:
		results[res.student_id]['totals'][res.category] = res.points
	gresults = lecture.getGradingResults(students = ls)
	grading_results = DictOfObjects(lambda: {})
	for res in gresults:
		grading_results[res.student_id][res.grading_id] = res.grade
	exams_by_category = [
		{'id':cat['id'], 'name': cat['name'], 'exams': lecture.exams.filter(models.Exam.category==cat['id']).all()} for cat in utils.categories]
	exams_by_category = [cat for cat in exams_by_category if cat['exams']]
	return {'lecture': lecture,
	        'lecture_students': ls.all(),
	        'categories': utils.categories,
	        'results': results,
	        'student_grades': grading_results,
	        'exams_by_category': exams_by_category,
	       }

@view_config(route_name='lecture_do_allocation', renderer='muesli.web:templates/lecture/do_allocation.pt', context=LectureContext, permission='edit')
def doAllocation(request):
	db = request.db
	lecture = request.context.lecture
	if not lecture.mode == 'prefs':
		return HTTPForbidden('This lecture is not in preferences mode')
	allocation = Allocation(lecture)
	result = allocation.doAllocation()
	prefs = {}
	for student in set(result['students_unhappy']+result['students_without_group']):
		p = [tp for tp in student.time_preferences if tp.lecture_id==lecture.id and tp.penalty < utils.students_unhappiness]
		prefs[student.id] = p
	lecture.mode = 'off'
	db.commit()
	return {'lecture': lecture,
			'result': result,
			'prefs': prefs}

@view_config(route_name='lecture_remove_allocation', context=LectureContext, permission='edit')
def removeAllocation(request):
	db = request.db
	lecture = request.context.lecture
	lecture.lecture_students.delete()
	lecture.mode = 'prefs'
	request.session.flash(u'Eintragung zurückgesetzt', queue='messages')
	db.commit()
	return HTTPFound(location=request.route_url('lecture_edit', lecture_id = lecture.id))


@view_config(route_name='lecture_set_preferences', context=LectureContext, permission='view')
def setPreferences(request):
	lecture = request.context.lecture
	times = lecture.prepareTimePreferences(user=request.user)
	row = 1
	tps = []
	while 'time-%i' % row in request.POST:
		time = types.TutorialTime(request.POST['time-%i' % row])
		tp = models.getOrCreate(models.TimePreference, request.db, (lecture.id, request.user.id, time))
		tp.penalty = int(request.POST['pref-%i' % row])
		tps.append(tp)
		row +=  1
	if lecture.minimum_preferences:
		valid = len(filter(lambda tp: tp.penalty < 100, tps)) >= lecture.minimum_preferences
	else:
		min_number_of_times = len(tps)/100.0+1
		penalty_count = sum([1.0/tp.penalty for tp in tps])
		valid = penalty_count > min_number_of_times
	if not valid:
		request.db.rollback()
		request.session.flash(u'Fehler: Sie haben zu wenige Zeiten ausgewählt', queue='errors')
	else:
		request.db.commit()
		request.session.flash(u'Präferenzen gespeichert.', queue='messages')
	return HTTPFound(location=request.route_url('lecture_view', lecture_id = lecture.id))

@view_config(route_name='lecture_remove_preferences', context=LectureContext, permission='view')
def removePreferences(request):
	lecture = request.context.lecture
	lecture.time_preferences.filter(models.TimePreference.student_id == request.user.id).delete()
	request.db.commit()
	request.session.flash(u'Präferenzen wurden entfernt.', queue='messages')
	return HTTPFound(location=request.route_url('lecture_view', lecture_id = lecture.id))

@view_config(route_name='lecture_view_points', renderer='muesli.web:templates/lecture/view_points.pt', context=LectureContext, permission='view_own_points')
def viewPoints(request):
	lecture = request.context.lecture
	try:
		ls = lecture.lecture_students.filter(models.LectureStudent.student_id == request.user.id).one()
	except exc.NoResultFound:
		return HTTPForbidden()
	exams = lecture.exams.all()
	exams_by_category = [
		{'id':cat['id'], 'name': cat['name'], 'exams': lecture.exams.filter(models.Exam.category==cat['id']).all()} for cat in utils.categories]
	exams_by_category = [cat for cat in exams_by_category if cat['exams']]
	results = {}
	for exam in exams:
		results[exam.id] = exam.getResultsForStudent(ls.student)
	for exams in exams_by_category:
		sum_all = sum(filter(lambda x:x, [results[e.id]['sum'] for e in exams['exams']]))
		max_all = sum(filter(lambda x:x, [e.getMaxpoints() for e in exams['exams']]))
		exams['sum'] = sum_all
		exams['max'] = max_all
	exams_with_registration = [e for e in lecture.exams.all() if e.registration != None]
	registrations = {}
	for reg in request.db.query(models.ExamAdmission).filter(models.ExamAdmission.exam_id.in_([e.id for e in exams_with_registration])).filter(models.ExamAdmission.student_id == ls.student_id).all():
		registrations[reg.exam_id] = reg
	for exam in exams_with_registration:
		if not exam.id in registrations:
			registrations[exam.id] = models.ExamAdmission(exam=exam, student=request.user)
		if 'registration-%s' % exam.id in request.POST:
			newreg = request.POST['registration-%s' % exam.id]
			if newreg=='':
				newreg=None
			registrations[exam.id].registration=newreg
			request.db.merge(registrations[exam.id])
			request.db.commit()
	exams_with_admission = [e for e in lecture.exams.all() if e.admission != None]
	admissions = {}
	for adm in request.db.query(models.ExamAdmission).filter(models.ExamAdmission.exam_id.in_([e.id for e in exams_with_admission])).filter(models.ExamAdmission.student_id == ls.student_id).all():
		admissions[adm.exam_id] = adm
	for exam in exams_with_admission:
		if not exam.id in admissions:
			admissions[exam.id] = models.ExamAdmission(exam=exam, student=request.user)
	grades = request.user.student_grades.filter(models.StudentGrade.grading.has(models.Grading.lecture_id == lecture.id)).all()
	return {
		'lecture': lecture,
		'results': results,
		'exams_by_category': exams_by_category,
		'registrations': registrations,
		'admissions': admissions,
		'grades': grades,
		}
	return HTTPFound(location=request.route_url('lecture_view', lecture_id = lecture.id))
