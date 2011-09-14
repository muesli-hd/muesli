# -*- coding: utf-8 -*-
#
# muesli/web/viewsGrading.py
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
from sqlalchemy.sql import func
import sqlalchemy

import re
import os

@view_config(route_name='grading_edit', renderer='muesli.web:templates/grading/edit.pt', context=GradingContext, permission='edit')
class Edit(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.grading_id = request.matchdict['grading_id']
	def __call__(self):
		grading = self.db.query(models.Grading).get(self.grading_id)
		form = GradingEdit(self.request, grading)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			form.saveValues()
			self.request.db.commit()
			form.message = u"Änderungen gespeichert."
		#if exam.admission!=None or exam.registration!=None:
		#	students = exam.lecture.lecture_students
		#	if exam.admission != None:
		#		students = students.filter(models.LectureStudent.student.has(models.User.exam_admissions.any(sqlalchemy.and_(models.ExamAdmission.exam_id==exam.id, models.ExamAdmission.admission==True))))
		#		print students.statement
		#	if exam.registration != None:
		#		students = students.filter(models.LectureStudent.student.has(models.User.exam_admissions.any(sqlalchemy.and_(models.ExamAdmission.exam_id==exam.id, models.ExamAdmission.registration==True))))
		#else: students = None
		return {'grading': grading,
		        'form': form,
		       }