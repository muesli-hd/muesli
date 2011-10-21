# -*- coding: utf-8 -*-
#
# muesli/web/viewsTutorial.py
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
from muesli.web.forms import *
from muesli.web.context import *

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden, HTTPFound
from pyramid.url import route_url
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from sqlalchemy.orm import exc
import sqlalchemy

import re
import os

import PIL.Image
import PIL.ImageDraw
import StringIO

@view_config(route_name='tutorial_view', renderer='muesli.web:templates/tutorial/view.pt', context=TutorialContext, permission='view')
class View(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.tutorial_ids = request.matchdict['tutorial_ids']
	def __call__(self):
		tutorials = [self.db.query(models.Tutorial).get(tutorial_id) for tutorial_id in self.tutorial_ids.split(',')]
		filterClause = models.User.lecture_students.any(models.LectureStudent.tutorial_id==tutorials[0].id)
		for tutorial in tutorials[1:]:
			filterClause = filterClause | (models.User.lecture_students.any(models.LectureStudent.tutorial_id==tutorial.id))
		students = self.db.query(models.User).filter(filterClause)
		tutorial = tutorials[0]
		return {'tutorial': tutorial,
		        'tutorials': tutorials,
		        'tutorial_ids': self.tutorial_ids,
		        'students': students,
		        'categories': utils.categories,
		        'exams': dict([[cat['id'], tutorial.lecture.exams.filter(models.Exam.category==cat['id'])] for cat in utils.categories]),
		        'names': utils.lecture_types[tutorial.lecture.type]}

@view_config(route_name='tutorial_occupancy_bar')
class OccupancyBar(object):
	def __init__(self, request):
		self.request = request
		self.count = int(request.matchdict['count'])
		self.max_count = int(request.matchdict['max_count'])
		self.max_count_total = int(request.matchdict['max_count_total'])
		self.width = 60
		self.height = 10
		self.color1 = (0,0,255)
		self.color2 = (140,140,255)
	def __call__(self):
		image = PIL.Image.new('RGB', (self.width,self.height),(255,255,255))
		draw = PIL.ImageDraw.Draw(image)
		draw.rectangle([(0,0),(float(self.width)*self.max_count/self.max_count_total,10)], fill=self.color2)
		draw.rectangle([(0,0),(float(self.width)*self.count/self.max_count_total,10)], fill=self.color1)
		output = StringIO.StringIO()
		image.save(output, format='PNG')
		response = Response()
		response.content_type = 'image/png'
		response.body = output.getvalue()
		output.close()
		return response

@view_config(route_name='tutorial_add', renderer='muesli.web:templates/tutorial/add.pt', context=LectureContext, permission='edit')
class Add(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
	def __call__(self):
		error_msg = ''
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		form = TutorialEdit(self.request, None)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			tutorial = models.Tutorial()
			tutorial.lecture = lecture
			form.obj = tutorial
			form.saveValues()
			self.request.db.commit()
			form.message = u"Neue Übungsgruppe angelegt."
		return {'lecture': lecture,
		        'names': utils.lecture_types[lecture.type],
		        'form': form,
		        'error_msg': error_msg}

@view_config(route_name='tutorial_edit', renderer='muesli.web:templates/tutorial/edit.pt', context=TutorialContext, permission='edit')
class Edit(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.tutorial_id = request.matchdict['tutorial_id']
	def __call__(self):
		error_msg = ''
		tutorial = self.db.query(models.Tutorial).get(self.tutorial_id)
		form = TutorialEdit(self.request, tutorial)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			form.saveValues()
			self.request.db.commit()
			form.message = u"Änderungen gespeichert"
		return {'tutorial': tutorial,
		        'names': utils.lecture_types[tutorial.lecture.type],
		        'form': form,
		        'error_msg': error_msg}

@view_config(route_name='tutorial_results', renderer='muesli.web:templates/tutorial/results.pt', context=TutorialContext, permission='view')
def results(request):
	tutorials = request.context.tutorials
	lecture = tutorials[0].lecture
	lecture_students = lecture.lecture_students_for_tutorials(tutorials=tutorials)
	lecture_results = lecture.getLectureResults(students=lecture_students)
	results = lecture.getPreparedLectureResults(lecture_results)
	cat_maxpoints = dict([cat['id'], 0] for cat in utils.categories)
	for exam in lecture.exams:
		cat_maxpoints[exam.category] += exam.getMaxpoints()
	return {'tutorials': tutorials,
	        'tutorial_ids': request.context.tutorial_ids,
	        'lecture_students': lecture_students,
	        'results': results,
	        'names': utils.lecture_types[lecture.type],
	        'categories': utils.categories,
	        'cat_maxpoints': cat_maxpoints,
	        'exams_by_cat': dict([[cat['id'], lecture.exams.filter(models.Exam.category==cat['id'])] for cat in utils.categories]),
	        }

@view_config(route_name='tutorial_subscribe', context=TutorialContext, permission='subscribe')
def subscribe(request):
	tutorials = request.context.tutorials
	tutorial = tutorials[0]
	lecture = tutorial.lecture
	if tutorial.max_students > tutorial.students.count():
		lrs = request.db.query(models.LectureRemovedStudent).get((lecture.id, request.user.id))
		if lrs: request.db.delete(lrs)
		ls = request.db.query(models.LectureStudent).get((lecture.id, request.user.id))
		if ls:
			oldtutorial = ls.tutorial
		else:
			ls = models.LectureStudent()
			ls.lecture = lecture
			ls.student = request.user
			oldtutorial = None
		ls.tutorial = tutorial
		if not ls in request.db: request.db.add(ls)
		request.db.commit()
		if oldtutorial:
			sendChangesMailUnsubscribe(request, oldtutorial, request.user, toTutorial=tutorial)
		sendChangesMailSubscribe(request, tutorial, request.user, fromTutorial=oldtutorial)
		request.session.flash(u'Erfolgreich in Übungsgruppe eingetragen', queue='messages')
	else:
		request.session.flash(u'Maximale Teilnehmerzahl bereits erreicht', queue='errors')
		pass
	return HTTPFound(location=request.route_url('lecture_view', lecture_id=lecture.id))

@view_config(route_name='tutorial_unsubscribe', context=TutorialContext, permission='unsubscribe')
def unsubscribe(request):
	tutorials = request.context.tutorials
	tutorial = tutorials[0]
	lecture = tutorial.lecture
	ls = request.db.query(models.LectureStudent).get((lecture.id, request.user.id))
	if not ls or ls.tutorial_id != tutorial.id:
		return HTTPForbidden('Sie sind zu dieser Übungsgruppe nicht angemeldet')
	lrs = request.db.query(models.LectureRemovedStudent).get((lecture.id, request.user.id))
	if not lrs:
		lrs = models.LectureRemovedStudent()
		lrs.lecture = lecture
		lrs.student = request.user
	lrs.tutorial = tutorial
	if not lrs in request.db: request.db.add(lrs)
	request.db.delete(ls)
	request.db.commit()
	sendChangesMailUnsubscribe(request, tutorial, request.user)
	request.session.flash(u'Erfolgreich aus Übungsgruppe ausgetragen', queue='messages')
	return HTTPFound(location=request.route_url('start'))

def sendChangesMailSubscribe(request, tutorial, student, fromTutorial=None):
	if not tutorial.tutor:
		return
	text = u'In Ihre Übungsgruppe zur Vorlesung %s am %s hat sich der Student %s eingetragen'\
		% (tutorial.lecture.name, tutorial.time, student.name())
	if fromTutorial:
		text += ' (Wechsel aus der Gruppe am %s von %s).' % (fromTutorial.time, fromTutorial.tutor.name() if fromTutorial.tutor else 'NN')
	else:
		text += '.'
	sendChangesMail(request, tutorial.tutor, text)
def sendChangesMailUnsubscribe(request, tutorial, student, toTutorial=None):
	if not tutorial.tutor:
		return
	text = u'Aus Ihrer Übungsgruppe zur Vorlesung %s am %s hat sich der Student %s ausgetragen'\
			% (tutorial.lecture.name, tutorial.time, student.name())
	if toTutorial:
		text += ' (Wechsel in die Gruppe am %s von %s).' % (toTutorial.time, toTutorial.tutor.name() if toTutorial.tutor else 'NN')
	else:
		text += '.'
	sendChangesMail(request, tutorial.tutor, text)

def sendChangesMail(request, tutor, text):
	mailer = get_mailer(request)
	message = Message(subject=u'MÜSLI: Änderungen in Ihrer Übungsgruppe',
		sender=u'MÜSLI-Team <muesli@mathi.uni-heidelberg.de>',
		recipients= [tutor.email],
		body=u'Hallo!\n\n%s\n\nMit freundlichen Grüßen,\n  Das MÜSLI-Team\n' % text)
	# As we are not using transactions,
	# we send the mail immediately.
	mailer.send_immediately(message)

@view_config(route_name='tutorial_email', renderer='muesli.web:templates/tutorial/email.pt', context=TutorialContext, permission='view')
def email(request):
	db = request.db
	tutorials = request.context.tutorials
	lecture = tutorials[0].lecture
	form = TutorialEmail()
	if request.method == 'POST' and form.processPostData(request.POST):
		lecture_students = lecture.lecture_students_for_tutorials(tutorials=tutorials)
		mailer = get_mailer(request)
		message = Message(subject=form['subject'],
			sender=request.user.email,
			recipients= [request.user.email],
			# Due to a bug, bcc does not work in pyramid_mailer at the moment.
			# Thus the email will be sent to the assistent only
			bcc=[ls.student.email for ls in lecture_students],
			body=form['body'])
		if request.POST['attachments'] not in ['', None]:
			a = Attachment(request.POST['attachments'].filename, data=request.POST['attachments'].file)
			message.attach(a)
		# As we are not using transactions,
		# we send the mail immediately.
		mailer.send_immediately(message)
		request.session.flash('A Mail has been send to all students of these tutorial', queue='messages')
	return {'tutorials': tutorials,
	        'tutorial_ids': request.context.tutorial_ids_str,
	        'lecture': lecture,
	        'form': form}