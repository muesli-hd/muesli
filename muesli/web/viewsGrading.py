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
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound
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
		return {'grading': grading,
		        'form': form,
		       }

@view_config(route_name='grading_associate_exam', context=GradingContext, permission='edit')
class AssociateExam(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.grading_id = request.matchdict['grading_id']
	def __call__(self):
		grading = self.db.query(models.Grading).get(self.grading_id)
		exam = self.db.query(models.Exam).get(self.request.POST['new_exam'])
		if grading.lecture_id == exam.lecture_id:
			if not exam in grading.exams:
				grading.exams.append(exam)
				self.db.commit()
		return HTTPFound(location=self.request.route_url('grading_edit', grading_id=grading.id))

@view_config(route_name='grading_delete_exam_association', context=GradingContext, permission='edit')
class DeleteExamAssociation(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.grading_id = request.matchdict['grading_id']
		self.exam_id = request.matchdict['exam_id']
	def __call__(self):
		grading = self.db.query(models.Grading).get(self.grading_id)
		exam = self.db.query(models.Exam).get(self.exam_id)
		if exam in grading.exams:
			grading.exams.remove(exam)
			self.db.commit()
		return HTTPFound(location=self.request.route_url('grading_edit', grading_id=grading.id))

@view_config(route_name='grading_enter_grades', renderer='muesli.web:templates/grading/enter_grades.pt', context=GradingContext, permission='edit')
class EnterGrades(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.grading_id = request.matchdict['grading_id']
	def __call__(self):
		grading = self.db.query(models.Grading).get(self.grading_id)
		formula = self.request.GET.get('formula', grading.formula)
		exam_id = self.request.GET.get('students', None)
		lecture_students = grading.lecture.lecture_students_for_tutorials([]).options(sqlalchemy.orm.joinedload(models.LectureStudent.student))
		gradesQuery = grading.student_grades.filter(models.StudentGrade.student_id.in_([ls.student_id for ls in lecture_students]))
		grades = DictOfObjects(lambda: {})
		exam_ids = [e.id for e in grading.exams]
		for ls in lecture_students:
			grades[ls.student_id]['grade'] = ''
			grades[ls.student_id]['invalid'] = None
			grades[ls.student_id]['exams'] = dict([[i, ''] for i in exam_ids])
		for grade in gradesQuery:
			grades[grade.student_id]['grade'] = grade
		for ls in lecture_students:
			if not grades[ls.student_id]['grade']:
				studentGrade = models.StudentGrade()
				studentGrade.student = ls.student
				studentGrade.grading = grading
				grades[ls.student_id]['grade'] = studentGrade
				self.db.add(studentGrade)
		if self.request.method == 'POST':
			for ls in lecture_students:
				param = 'grade-%u' % (ls.student_id)
				if param in self.request.POST:
					value = self.request.POST[param]
					if not value:
						grades[ls.student_id]['grade'].grade = None
					else:
						value = value.replace(',','.')
						try:
							value = float(value)
							grades[ls.student_id]['grade'].grade = value
						except:
							error_msgs.append('Could not convert "%s" (%s)'%(value, ls.student.name()))
		self.db.commit()
		for exam in grading.exams:
			results = exam.getResults(students = lecture_students)
			for result in results:
				grades[result.student_id]['exams'][exam.id] = result.points
		examvars = dict([['$%i' % i, e.id] for i,e in enumerate(grading.exams)])
		varsForExam = dict([[examvars[var], var] for var in examvars ])
		error_msgs = []
		self.request.javascript.add('prototype.js')
		return {'grading': grading,
		        'error_msg': '\n'.join(error_msgs),
		        'formula': formula,
		        'exam_id': exam_id,
		        'tutorial_ids': '',
		        'grades': grades,
		        'examvars': examvars,
		        'varsForExam': varsForExam,
		        'lecture_students': lecture_students}