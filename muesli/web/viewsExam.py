# -*- coding: utf-8 -*-
#
# muesli/web/viewsExam.py
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

@view_config(route_name='exam_edit', renderer='muesli.web:templates/exam/edit.pt', context=ExamContext, permission='edit')
class Edit(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.exam_id = request.matchdict['exam_id']
	def __call__(self):
		exam = self.db.query(models.Exam).get(self.exam_id)
		form = LectureEditExam(self.request, exam)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			form.saveValues()
			self.request.db.commit()
			form.message = u"Änderungen gespeichert."
		if exam.admission!=None or exam.registration!=None:
			students = exam.lecture.lecture_students
			if exam.admission != None:
				students = students.filter(models.LectureStudent.student.has(models.User.exam_admissions.any(sqlalchemy.and_(models.ExamAdmission.exam_id==exam.id, models.ExamAdmission.admission==True))))
				print students.statement
			if exam.registration != None:
				students = students.filter(models.LectureStudent.student.has(models.User.exam_admissions.any(sqlalchemy.and_(models.ExamAdmission.exam_id==exam.id, models.ExamAdmission.registration==True))))
		else: students = None
		return {'exam': exam,
		        'form': form,
		        'students': students
		       }

@view_config(route_name='exam_add_or_edit_exercise', renderer='muesli.web:templates/exam/add_or_edit_exercise.pt', context=ExamContext, permission='edit')
class AddOrEditExercise(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.exam_id = request.matchdict['exam_id']
		self.exercise_id = request.matchdict.get('exercise_id', None)
	def __call__(self):
		exam = self.db.query(models.Exam).get(self.exam_id)
		if self.exercise_id:
			exercise = self.db.query(models.Exercise).get(self.exercise_id)
		else: exercise = None
		form = ExamAddOrEditExercise(self.request, exercise)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			if exercise == None:
				exercise = models.Exercise()
				exercise.exam = exam
				form.obj = exercise
				creating = True
			else: creating = False
			form.saveValues()
			self.request.db.commit()
			if creating: form['nr'] = form['nr'] + 1
			form.message = u"Änderungen gespeichert."
		return {'form': form,
		        'exam': exam}

@view_config(route_name='exam_enter_points', renderer='muesli.web:templates/exam/enter_points.pt', context=ExamContext, permission='enter_points')
class EnterPoints(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.exam_id = request.matchdict['exam_id']
		self.tutorial_ids = request.matchdict['tutorial_ids'].split(',')
		if len(self.tutorial_ids)==1 and self.tutorial_ids[0]=='':
			self.tutorial_ids = []
	def __call__(self):
		error_msgs = []
		exam = self.db.query(models.Exam).get(self.exam_id)
		tutorials = [self.db.query(models.Tutorial).get(tutorial_id) for tutorial_id in self.tutorial_ids]
		students = exam.lecture.lecture_students_for_tutorials(tutorials).join(models.User).order_by(models.User.last_name, models.User.first_name).options(sqlalchemy.orm.joinedload(LectureStudent.student))
		pointsQuery = exam.exercise_points.filter(ExerciseStudent.student_id.in_([s.student.id for s  in students])).options(sqlalchemy.orm.joinedload(ExerciseStudent.student, ExerciseStudent.exercise))
		points = DictOfObjects(lambda: {})
		#for s in students:
		#	for e in exam.exercises:
		#		points[s.student_id][e.id] = None
		for point in pointsQuery:
			points[point.student_id][point.exercise_id] = point
		if self.request.method == 'POST':
			for student in students:
				for e in exam.exercises:
					if not e.id in points[student.student_id]:
						exerciseStudent = models.ExerciseStudent()
						exerciseStudent.student = student.student
						exerciseStudent.exercise = e
						points[student.student_id][e.id] = exerciseStudent
						self.db.add(exerciseStudent)
					param = 'points-%u-%u' % (student.student_id, e.id)
					if param in self.request.POST:
						value = self.request.POST[param]
						if not value:
							points[student.student_id][e.id].points = None
						else:
							value = value.replace(',','.')
							try:
								value = float(value)
								points[student.student_id][e.id].points = value
							except:
								error_msgs.append('Could not convert "%s" (%s, Exercise %i)'%(value, student.student.name(), e.nr))
			self.db.commit()
		for student in points:
			points[student]['total'] = sum([v.points for v in points[student].values() if v.points])
		# TODO: Die Statistik scheint recht langsm zu sein. Evt lohnt es sich,
		#       die selber auszurechnen...
		statistics = exam.getStatistics(students=students)
		return {'exam': exam,
		        'tutorial_ids': self.request.matchdict['tutorial_ids'],
		        'students': students,
		        'points': points,
		        'statistics': statistics,
		        'error_msg': '\n'.join(error_msgs)}

@view_config(route_name='exam_export', renderer='muesli.web:templates/exam/export.pt', context=ExamContext, permission='enter_points')
class Export(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.exam_id = request.matchdict['exam_id']
		self.tutorial_ids = request.matchdict['tutorial_ids'].split(',')
		if len(self.tutorial_ids)==1 and self.tutorial_ids[0]=='':
			self.tutorial_ids = []
	def __call__(self):
		exam = self.db.query(models.Exam).get(self.exam_id)
		tutorials = [self.db.query(models.Tutorial).get(tutorial_id) for tutorial_id in self.tutorial_ids]
		students = exam.lecture.lecture_students_for_tutorials(tutorials).options(sqlalchemy.orm.joinedload(LectureStudent.student))
		pointsQuery = exam.exercise_points.filter(ExerciseStudent.student_id.in_([s.student.id for s  in students])).options(sqlalchemy.orm.joinedload(ExerciseStudent.student, ExerciseStudent.exercise))
		points = DictOfObjects(lambda: {})
		for point in pointsQuery:
			points[point.student_id][point.exercise_id] = point
		for student in students:
			for e in exam.exercises:
				if not e.id in points[student.student_id]:
					exerciseStudent = models.ExerciseStudent()
					exerciseStudent.student = student.student
					exerciseStudent.exercise = e
					points[student.student_id][e.id] = exerciseStudent
					self.db.add(exerciseStudent)
		self.db.commit()
		for student in points:
			points[student]['total'] = sum([v.points for v in points[student].values() if v.points])
		return {'exam': exam,
		        'tutorial_ids': self.request.matchdict['tutorial_ids'],
		        'students': students,
		        'points': points}
