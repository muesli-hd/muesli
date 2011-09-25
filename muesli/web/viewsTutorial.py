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
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.url import route_url
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
