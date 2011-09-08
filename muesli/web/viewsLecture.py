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
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.url import route_url
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

@view_config(route_name='lecture_edit', renderer='muesli.web:templates/lecture/edit.pt', context=LectureContext, permission='edit')
class Edit(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
		self.form = Form(UserLogin())
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		names = utils.lecture_types[lecture.type]
		formdata = [
			FormField('type',
			   label='Typ',
			   type='select',
			   options=[[type, utils.lecture_types[type]['name']] for type in utils.lecture_types],
			   value=lecture.type),
			FormField('name',
			   label='Name',
			   type='text',
			   size=100,
			   value=lecture.name),
			FormField('term',
			   label='Semester',
			   type='select',
			   options=utils.getTerms(),
			   value=lecture.term),
			FormField('lsf_id',
			   label='Veranstaltungsnummer',
			   type='text',
			   size=20,
			   value=lecture.lsf_id),
			FormField('lecturer',
			   label='Dozent',
			   type='text',
			   size=40,
			   value=lecture.lecturer),
			FormField('url',
			   label='Homepage',
			   size=100,
			   value=lecture.url),
			FormField('mode',
			   label='Anmeldemodus',
			   type='select',
			   options=utils.modes,
			   value=lecture.mode),
			FormField('minimum_preferences',
			   label=u'Minimum möglicher Termine',
			   size=5,
			   comment=u'Bei Präferenzenanmeldung: Studenten müssen mindestens an soviel Terminen können. (Leer: Defaultformel)',
			   value=lecture.minimum_preferences),
			FormField('password',
			   label=u'Passwort für Übungsleiter',
			   size=40,
			   comment=u'Bei leerem Passwort keine Anmeldung als Übungsleiter möglich',
			   value=lecture.password),
			FormField('is_visible',
			   label='Sichtbar',
			   type='radio',
			   options=[[1, 'Ja'], [0, 'Nein']],
			   value=1 if lecture.is_visible else 0)]
		if self.request.permissionInfo.has_permission('change_assistant'):
			assistants = self.db.query(models.User).filter(models.User.is_assistant==1).all()
			formdata.append(
			  FormField('assistant',
			   label='Assistent',
			   type='select',
			   options=[[a.id, a.name()] for a in assistants],
			   value=lecture.assistant.id))
		pref_subjects = lecture.pref_subjects()
		pref_count = sum([pref[0] for pref in pref_subjects])
		subjects = lecture.subjects()
		student_count = sum([subj[0] for subj in subjects])
		return {'lecture': lecture,
		        'names': names,
		        'formdata': formdata,
		        'pref_subjects': pref_subjects,
		        'pref_count': pref_count,
		        'subjects': subjects,
		        'student_count': student_count,
		        'categories': utils.categories,
		        'exams': dict([[cat['id'], lecture.exams.filter(models.Exam.category==cat['id'])] for cat in utils.categories]),
		        'form': self.form}