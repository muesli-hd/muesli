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
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		form = LectureEdit(self.request, lecture)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			lecture.type =     form['type']
			lecture.name =     form['name']
			lecture.term =     form['term']
			lecture.lsf_id =   form['lsf_id']
			lecture.lecturer = form['lecturer']
			lecture.url =      form['url']
			lecture.mode =     form['mode']
			lecture.minimum_preferences = form['minimum_preferences']
			lecture.password = form['password']
			lecture.is_visible=form['is_visible']==1
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