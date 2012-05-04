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
from muesli.parser import Parser
from muesli.web.context import *
from muesli.web.forms import *

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound
from pyramid.url import route_url
from sqlalchemy.orm import exc
from sqlalchemy.sql import func
import sqlalchemy

import pyExcelerator

import re
import os
import StringIO
import datetime

@view_config(route_name='grading_edit', renderer='muesli.web:templates/grading/edit.pt', context=GradingContext, permission='edit')
class Edit(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
	def __call__(self):
		grading = self.request.context.grading
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
	def __call__(self):
		grading = self.request.context.grading
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
		self.exam_id = request.matchdict['exam_id']
	def __call__(self):
		grading = self.request.context.grading
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
	def __call__(self):
		grading = self.request.context.grading
		formula = self.request.GET.get('formula', None)
		if formula:
			grading.formula = formula
			self.db.commit()
		else:
			formula = grading.formula
		exam_id = self.request.GET.get('students', None)
		if exam_id:
			exam = self.request.db.query(models.Exam).get(exam_id)
		else: exam=None
		lecture_students = grading.lecture.lecture_students_for_tutorials([])\
			.options(sqlalchemy.orm.joinedload(models.LectureStudent.student))
		if exam:
			lecture_students = lecture_students\
				.join(models.ExerciseStudent, models.LectureStudent.student_id==models.ExerciseStudent.student_id)\
				.join(models.Exercise)\
				.join(models.Exam)\
				.filter(models.Exam.id==exam_id)
		lecture_students = lecture_students.all()
		gradesQuery = grading.student_grades.filter(models.StudentGrade.student_id.in_([ls.student_id for ls in lecture_students]))
		grades = DictOfObjects(lambda: {})
		exam_ids = [e.id for e in grading.exams]
		examvars = dict([['$%i' % i, e.id] for i,e in enumerate(grading.exams)])
		varsForExam = dict([[examvars[var], var] for var in examvars ])
		for ls in lecture_students:
			grades[ls.student_id]['grade'] = ''
			grades[ls.student_id]['gradestr'] = ''
			grades[ls.student_id]['invalid'] = None
			grades[ls.student_id]['exams'] = dict([[i, ''] for i in exam_ids])
			grades[ls.student_id]['calc'] = ''
		for grade in gradesQuery:
			grades[grade.student_id]['grade'] = grade
			grades[grade.student_id]['gradestr'] = grade.grade
		#for ls in lecture_students:
		#	if not grades[ls.student_id]['grade']:
		#		studentGrade = models.StudentGrade()
		#		studentGrade.student = ls.student
		#		studentGrade.grading = grading
		#		grades[ls.student_id]['grade'] = studentGrade
		#		self.db.add(studentGrade)
		if self.request.method == 'POST':
			for ls in lecture_students:
				param = 'grade-%u' % (ls.student_id)
				if param in self.request.POST:
					value = self.request.POST[param]
					if not grades[ls.student_id]['grade']:
						studentGrade = models.StudentGrade()
						studentGrade.student = ls.student
						studentGrade.grading = grading
						grades[ls.student_id]['grade'] = studentGrade
						self.db.add(studentGrade)
					if not value:
						grades[ls.student_id]['grade'].grade = None
						grades[ls.student_id]['gradestr'] = ''
					else:
						value = value.replace(',','.')
						try:
							value = float(value)
							grades[ls.student_id]['grade'].grade = value
							grades[ls.student_id]['gradestr'] = value
						except:
							error_msgs.append('Could not convert "%s" (%s)'%(value, ls.student.name()))
		if self.db.new or self.db.dirty or self.db.deleted:
			self.db.commit()
		for exam in grading.exams:
			results = exam.getResults(students = lecture_students)
			for result in results:
				grades[result.student_id]['exams'][exam.id] = result.points
		error_msgs = []
		if formula:
			parser = Parser()
			try:
				parser.parseString(formula)
				for ls in lecture_students:
				#print student
					d = {}
					for exam in grading.exams:
						result = grades[ls.student_id]['exams'][exam.id]
						if result == '':
							result = None
						d[varsForExam[exam.id]] = result
					result = parser.calculate(d)
					grades[ls.student_id]['calc'] = result if result != None else ''
					if 'fill' in self.request.GET:
						grades[ls.student_id]['gradestr'] = result if result != None else ''
			except Exception, err:
				error_msgs.append(str(err))
		if 'fill' in self.request.GET:
			self.request.session.flash('Achtung, die Noten sind noch nicht abgespeichert!', queue='errors')
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

class ExcelView(object):
	def __init__(self, request):
		self.request = request
		self.w = pyExcelerator.Workbook()
	def createResponse(self):
		output = StringIO.StringIO()
		self.w.save(output)
		response = Response(content_type='application/vnd.ms-excel')
		response.body = output.getvalue()
		output.close()
		return response

@view_config(route_name='grading_export', context=GradingContext, permission='edit')
class Export(ExcelView):
	def __call__(self):
		grading = self.request.context.grading
		lecture = grading.lecture
		w = self.w
		worksheet_exams = w.add_sheet('Pruefung')
		worksheet_exams.set_col_default_width(20)
		header_style = pyExcelerator.XFStyle()
		header_style.font.bold=True
		date_style = pyExcelerator.XFStyle()
		date_style.num_format_str = 'dd.mm.yyyy'
		header = ['Tabellenname', 'Veranstaltungsnummer', 'Titel', 'Semester', 'Termin', 'Datum', 'PrueferId', 'Pruefername']
		for i,h in enumerate(header):
			worksheet_exams.write(0,i,h,header_style)
		data = ['Pruefungsteilnehmer',
			lecture.lsf_id,
			lecture.name,
			str(lecture.term) if lecture.term!=None else '',
			grading.hispos_type,
			None,
			grading.examiner_id,
			lecture.lecturer]
		for i,d in enumerate(data):
			worksheet_exams.write(1,i,d if d != None else '')
		date_p = re.compile('(\d{1,2}).(\d{1,2}).(\d{4})$')
		m = date_p.match(grading.hispos_date or '')
		if m:
			date = datetime.datetime(year=int(m.group(3)), month=int(m.group(2)), day=int(m.group(1)))
			worksheet_exams.write(1,5,date, date_style)
		worksheet_grades =self.w.add_sheet('Pruefungsteilnehmer')
		worksheet_grades.set_col_default_width(16)
		header = ['mtknr', 'name', 'stg', 'stg_txt', 'accnr', 'pnr', 'pnote', 'pstatus', 'ppunkte', 'pbonus']
		for i,h in enumerate(header):
			worksheet_grades.write(0,i,h,header_style)
		grades = grading.student_grades.options(sqlalchemy.orm.joinedload(models.StudentGrade.student)).all()
		for i,grade in enumerate(grades):
			if grade.grade != None:
				g = float(grade.grade*100)
			else:
				g = ''
			data = [grade.student.matrikel, grade.student.last_name, '', grade.student.formatCompleteSubject(), '', '', g, '']
			for j,d in enumerate(data):
				worksheet_grades.write(1+i,j,d if d != None else '')
		worksheet_data = self.w.add_sheet('Daten')
		worksheet_data.set_col_default_width(17)
		header = ['Matrikel', 'Nachname', 'Vorname', 'Geburtsort', 'Geburtsdatum', 'Note', 'Vortragstitel', 'Studiengang']
		for i,h in enumerate(header):
			worksheet_data.write(0,i,h,header_style)
		for i,grade in enumerate(grades):
			m = date_p.match(grade.student.birth_date or '')
			if m: date = datetime.datetime(year=int(m.group(3)), month=int(m.group(2)), day=int(m.group(1)))
			else: date = ''
			data = [grade.student.matrikel,
				grade.student.last_name,
				grade.student.first_name,
				grade.student.birth_place,
				None,
				float(grade.grade) if grade.grade != None else '',
				'',
				grade.student.formatCompleteSubject()]
			for j,d in enumerate(data):
				worksheet_data.write(1+i,j,d if d != None else '')
			worksheet_data.write(1+i,4, date, date_style)
		return self.createResponse()
