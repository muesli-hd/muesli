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
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound
from pyramid.url import route_url
from sqlalchemy.orm import exc
from sqlalchemy.sql import func
import sqlalchemy

import PIL.Image
import PIL.ImageDraw
import StringIO

import matplotlib
matplotlib.use( 'Agg' )
from matplotlib import pyplot

import re
import os
import math

@view_config(route_name='exam_edit', renderer='muesli.web:templates/exam/edit.pt', context=ExamContext, permission='edit')
class Edit(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
	def __call__(self):
		exam = self.request.context.exam
		form = LectureEditExam(self.request, exam)
		if self.request.method == 'POST' and form.processPostData(self.request.POST):
			form.saveValues()
			self.request.db.commit()
			form.message = u"Änderungen gespeichert."
		if exam.admission!=None or exam.registration!=None:
			students = exam.lecture.lecture_students.options(sqlalchemy.orm.joinedload(LectureStudent.student))\
				.options(sqlalchemy.orm.joinedload_all('tutorial.tutor'))
			if exam.admission != None:
				students = students.filter(models.LectureStudent.student.has(models.User.exam_admissions.any(sqlalchemy.and_(models.ExamAdmission.exam_id==exam.id, models.ExamAdmission.admission==True))))
			if exam.registration != None:
				students = students.filter(models.LectureStudent.student.has(models.User.exam_admissions.any(sqlalchemy.and_(models.ExamAdmission.exam_id==exam.id, models.ExamAdmission.registration==True))))
		else: students = None
		return {'exam': exam,
		        'form': form,
		        'students': students
		       }

@view_config(route_name='exam_delete', context=ExamContext, permission='edit')
def delete(request):
	exam = request.context.exam
	if exam.exercises:
		request.session.flash(u'Dieses Testat hat noch Aufgaben!', queue='errors')
	else:
		request.db.delete(exam)
		request.db.commit()
		request.session.flash(u'Testat gelöscht!', queue='messages')
	return HTTPFound(location=request.route_url('lecture_edit', lecture_id = exam.lecture.id))

@view_config(route_name='exam_add_or_edit_exercise', renderer='muesli.web:templates/exam/add_or_edit_exercise.pt', context=ExamContext, permission='edit')
class AddOrEditExercise(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.exercise_id = request.matchdict.get('exercise_id', None)
	def __call__(self):
		exam = self.request.context.exam
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

@view_config(route_name='exam_delete_exercise', context=ExamContext, permission='edit')
class DeleteExercise(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.exercise_id = request.matchdict['exercise_id']
	def __call__(self):
		exam = self.request.context.exam
		exercise = self.db.query(models.Exercise).get(self.exercise_id)
		points = exercise.exercise_points.all()
		none_points = [p.points == None for p in points]
		if not all(none_points):
			self.request.session.flash(u'Für diese Aufgabe sind bereits Punkte eingetragen!', queue='errors')
		else:
			for point in points:
				self.request.db.delete(point)
			self.request.db.delete(exercise)
			self.request.db.commit()
			self.request.session.flash(u'Aufgabe gelöscht', queue='messages')
		return HTTPFound(location=self.request.route_url('exam_edit', exam_id = exam.id))

class EnterPointsBasic(object):
	def __init__(self, request, raw=False):
		self.request = request
		self.db = self.request.db
		self.tutorial_ids = self.request.context.tutorial_ids
		self.raw = raw
	def __call__(self):
		error_msgs = []
		exam = self.request.context.exam
		tutorials = self.request.context.tutorials
		students = exam.lecture.lecture_students_for_tutorials(tutorials).options(sqlalchemy.orm.joinedload(LectureStudent.student))\
					.options(sqlalchemy.orm.joinedload_all('tutorial.tutor'))
		students = students.all()
		if 'students' in self.request.GET:
			student_ids = self.request.GET['students'].split(',')
			student_ids = [int(sid.strip()) for sid in student_ids]
			students = [s for s in students if s.student.id in student_ids]
		pointsQuery = exam.exercise_points.filter(ExerciseStudent.student_id.in_([s.student.id for s  in students])).options(sqlalchemy.orm.joinedload(ExerciseStudent.student), sqlalchemy.orm.joinedload(ExerciseStudent.exercise))
		points = DictOfObjects(lambda: {})
		#for s in students:
		#	for e in exam.exercises:
		#		points[s.student_id][e.id] = None
		for point in pointsQuery.all():
			points[point.student_id][point.exercise_id] = point
		for student in students:
			if not student.student_id in points:
				points[student.student_id] = {}
			for e in exam.exercises:
				if not e.id in points[student.student_id]:
					exerciseStudent = models.ExerciseStudent()
					exerciseStudent.student = student.student
					exerciseStudent.exercise = e
					points[student.student_id][e.id] = exerciseStudent
					self.db.add(exerciseStudent)
		if self.request.method == 'POST':
			if not self.request.permissionInfo.has_permission('enter_points'):
				return HTTPForbidden('Sie haben keine Rechte um Punkte einzutragen!')
			for student in students:
				for e in exam.exercises:
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
								error_msgs.append(u'Could not convert "%s" (%s, Exercise %i)'%(value, student.student.name(), e.nr))
		for student in points:
			points[student]['total'] = sum([v.points for v in points[student].values() if v.points])
		if self.db.new or self.db.dirty or self.db.deleted:
			self.db.commit()
		# TODO: Die Statistik scheint recht langsm zu sein. Evt lohnt es sich,
		#       die selber auszurechnen...
		if tutorials:
			statistics = exam.getStatistics(students=None)
			statistics.update(exam.getStatistics(students=students, prefix='tut'))
		else:
			statistics = exam.getStatistics(students=students)
		if not self.raw:
			self.request.javascript.add('prototype.js')
		return {'exam': exam,
		        'tutorial_ids': self.request.matchdict['tutorial_ids'],
		        'students': students,
		        'points': points,
		        'statistics': statistics,
		        'error_msg': u'\n'.join(error_msgs)}

@view_config(route_name='exam_enter_points', renderer='muesli.web:templates/exam/enter_points.pt', context=ExamContext, permission='view_points')
class EnterPoints(EnterPointsBasic):
	def __init__(self, request):
		super(EnterPoints, self).__init__(request, raw=False)

@view_config(route_name='exam_enter_points_raw', renderer='muesli.web:templates/exam/enter_points_raw.pt', context=ExamContext, permission='view_points')
class EnterPointsRaw(EnterPointsBasic):
	def __init__(self, request):
		super(EnterPointsRaw, self).__init__(request, raw=True)

@view_config(route_name='exam_admission', renderer='muesli.web:templates/exam/admission.pt', context=ExamContext, permission='view_points')
class Admission(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.tutorial_ids = self.request.context.tutorial_ids
	def valueToBool(self, value):
		if value=='1':
			return True
		if value=='0':
			return False
		if value=='':
			return None
		raise ValueError('"%r" could not be converted to boolean' % value)
	def __call__(self):
		error_msgs = []
		exam = self.request.context.exam
		tutorials = self.request.context.tutorials
		students = exam.lecture.lecture_students_for_tutorials(tutorials).options(sqlalchemy.orm.joinedload(LectureStudent.student))\
					.options(sqlalchemy.orm.joinedload_all('tutorial.tutor'))
		students = students.all()
		db_admissions = exam.exam_admissions.filter(ExamAdmission.student_id.in_([s.student.id for s  in students])).all()
		admissions={}
		for admission in db_admissions:
			admissions[admission.student_id] = admission
		for student in students:
			if not student.student_id in admissions:
				admission = ExamAdmission(exam, student.student)
				self.db.add(admission)
				admissions[student.student_id] = admission
		if self.request.method == 'POST':
			if not self.request.permissionInfo.has_permission('enter_points'):
				return HTTPForbidden('Sie haben keine Rechte um Punkte einzutragen!')
			for ls in students:
				admission_parameter = 'admission-{0}'.format(ls.student_id)
				if exam.admission and admission_parameter in self.request.POST:
					admissions[ls.student_id].admission = self.valueToBool(self.request.POST[admission_parameter])
				registration_parameter = 'registration-{0}'.format(ls.student_id)
				if exam.registration and registration_parameter in self.request.POST:
					admissions[ls.student_id].registration = self.valueToBool(self.request.POST[registration_parameter])
				certificate_parameter = 'medical_certificate-{0}'.format(ls.student_id)
				if exam.medical_certificate and certificate_parameter in self.request.POST:
					admissions[ls.student_id].medical_certificate = self.valueToBool(self.request.POST[certificate_parameter])
		if self.db.new or self.db.dirty or self.db.deleted:
			self.db.commit()
		return {'exam': exam,
		        'tutorial_ids': self.request.matchdict['tutorial_ids'],
		        'students': students,
		        'admissions': admissions,
		        }

@view_config(route_name='exam_export', renderer='muesli.web:templates/exam/export.pt', context=ExamContext, permission='view_points')
class Export(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.tutorial_ids = request.context.tutorial_ids
	def __call__(self):
		exam = self.request.context.exam
		tutorials = self.request.context.tutorials
		students = exam.lecture.lecture_students_for_tutorials(tutorials).options(sqlalchemy.orm.joinedload(LectureStudent.student)).all()
		pointsQuery = exam.exercise_points.filter(ExerciseStudent.student_id.in_([s.student.id for s  in students])).options(sqlalchemy.orm.joinedload(ExerciseStudent.student), sqlalchemy.orm.joinedload(ExerciseStudent.exercise))
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
		if self.db.new or self.db.dirty or self.db.deleted:
			self.db.commit()
		for student in points:
			points[student]['total'] = sum([v.points for v in points[student].values() if v.points])
		if exam.admission!=None or exam.registration!=None or exam.medical_certificate!=None:
			admissions = exam.exam_admissions
			for a in admissions:
				if exam.admission!=None:
					points[a.student_id]['admission'] = a.admission
				if exam.registration!=None:
					points[a.student_id]['registration'] = a.registration
				if exam.medical_certificate!=None:
					points[a.student_id]['medical_certificate'] = a.medical_certificate
			for student in points:
				if exam.admission!=None and not 'admission' in points[student]:
					points[student]['admission'] = None
				if exam.registration!=None and not 'registration' in points[student]:
					points[student]['registration'] = None
				if exam.medical_certificate!=None and not 'medical_certificate' in points[student]:
					points[student]['medical_certificate'] = None
		return {'exam': exam,
		        'tutorial_ids': self.request.matchdict['tutorial_ids'],
		        'students': students,
		        'points': points}


@view_config(route_name='exam_statistics', renderer='muesli.web:templates/exam/statistics.pt', context=ExamContext, permission='statistics')
def statistics(request):
	db = request.db
	tutorial_ids = request.context.tutorial_ids
	exam = request.context.exam
	tutorials = request.context.tutorials
	lecturestudents = exam.lecture.lecture_students.all()
	statistics = exam.getStatistics(students=lecturestudents)
	statistics_by_subject = exam.getStatisticsBySubjects(students=lecturestudents)# exam.getStatisticsBySubject(students=students)
	if tutorials:
		tutorialstudents = exam.lecture.lecture_students_for_tutorials(tutorials).options(sqlalchemy.orm.joinedload(LectureStudent.student))
		tutstat = exam.getStatistics(students=tutorialstudents, prefix='tut')
		statistics.update(exam.getStatistics(students=tutorialstudents, prefix='tut'))
		old_statistics_by_subject = statistics_by_subject
		statistics_by_subject = exam.getStatisticsBySubjects(students=tutorialstudents, prefix='tut')
		statistics_by_subject.update_available(old_statistics_by_subject)
	admissions = {}
	if exam.admission!=None or exam.registration!=None or exam.medical_certificate!=None:
		admission_data = exam.exam_admissions.all()
		all_student_ids = [ls.student_id for ls in lecturestudents]
		if exam.admission!=None:
			admissions['admission_count'] = len([e for e in admission_data if e.admission and e.student_id in all_student_ids])
		if exam.registration!=None:
			admissions['registration_count'] = len([e for e in admission_data if e.registration and e.student_id in all_student_ids])
		if exam.admission!=None and exam.registration!=None:
			admissions['admission_and_registration_count'] = len([e for e in admission_data if e.admission and e.registration and e.student_id in all_student_ids])
		if exam.medical_certificate!=None:
			admissions['medical_certificate_count'] = len([e for e in admission_data if e.medical_certificate and e.student_id in all_student_ids])
		if tutorials:
			student_ids = [s.student_id for s in tutorialstudents]
			if exam.admission!=None:
				admissions['admission_count_tut'] = len([e for e in admission_data if e.admission and e.student_id in student_ids])
			if exam.registration!=None:
				admissions['registration_count_tut'] = len([e for e in admission_data if e.registration and e.student_id in student_ids])
			if exam.admission!=None and exam.registration!=None:
				admissions['admission_and_registration_count_tut'] = len([e for e in admission_data if e.registration and e.admission and e.student_id in student_ids])
			if exam.medical_certificate!=None:
				admissions['medical_certificate_count_tut'] = len([e for e in admission_data if e.medical_certificate and e.student_id in student_ids])
	quantils = []
	for q in exam.getQuantils():
		quantils.append({'lecture': q})
	if tutorials:
		for i,q in enumerate(exam.getQuantils(students=tutorialstudents)):
			quantils[i]['tutorial'] = q
		#quantils['tutorials'] = exam.getQuantils(students=tutorialstudents)
	request.javascript.add('prototype.js')
	#pointsQuery = exam.exercise_points.filter(ExerciseStudent.student_id.in_([s.student.id for s  in students])).options(sqlalchemy.orm.joinedload(ExerciseStudent.student, ExerciseStudent.exercise))
	#points = DictOfObjects(lambda: {})
	#for point in pointsQuery:
		#points[point.student_id][point.exercise_id] = point
	#for student in students:
		#for e in exam.exercises:
			#if not e.id in points[student.student_id]:
				#exerciseStudent = models.ExerciseStudent()
				#exerciseStudent.student = student.student
				#exerciseStudent.exercise = e
				#points[student.student_id][e.id] = exerciseStudent
				#self.db.add(exerciseStudent)
	#self.db.commit()
	#for student in points:
		#points[student]['total'] = sum([v.points for v in points[student].values() if v.points])
	return {'exam': exam,
			'tutorial_ids': request.matchdict['tutorial_ids'],
			#'students': students,
			'quantils': quantils,
			'admissions': admissions,
			'statistics': statistics,
			'statistics_by_subject': statistics_by_subject}

@view_config(route_name='exam_statistics_bar')
class ExamStatisticsBar(object):
	def __init__(self, request):
		self.request = request
		self.width = 60
		self.height = 10
		self.color1 = (0,0,255)
		self.color2 = (140,140,255)
		self.max = float(request.matchdict['max'])
		self.lecture_points = float(request.matchdict['lecture_points'])
		self.tutorial_points = float(request.matchdict['tutorial_points'])\
			if (request.matchdict['tutorial_points']!=None and request.matchdict['tutorial_points']!='') else None
		self.values = [[self.lecture_points, self.max]]
		if self.tutorial_points != None:
			self.values.insert(0,[self.tutorial_points, self.max])
	def __call__(self):
		image = PIL.Image.new('RGB', (self.width,self.height),(255,255,255))
		draw = PIL.ImageDraw.Draw(image)
		barheight = float(self.height)/len(self.values)
		for i,bar in enumerate(self.values):
			draw.rectangle([(0,i*barheight),(float(self.width)*bar[1]/self.max,(i+1)*barheight)], fill=self.color2)
			draw.rectangle([(0,i*barheight),(float(self.width)*bar[0]/self.max,(i+1)*barheight)], fill=self.color1)
		output = StringIO.StringIO()
		image.save(output, format='PNG')
		response = Response()
		response.content_type = 'image/png'
		response.body = output.getvalue()
		output.close()
		return response

class MatplotlibView(object):
	def __init__(self):
		self.fig = pyplot.figure()
	def createResponse(self):
		output = StringIO.StringIO()
		self.fig.savefig(output, format='png', dpi=50, bbox_inches='tight')
		pyplot.close(self.fig)
		response = Response()
		response.content_type = 'image/png'
		response.body = output.getvalue()
		output.close()
		return response

class Histogram(MatplotlibView):
	def __init__(self, request):
		MatplotlibView.__init__(self)
		self.request = request
		self.points = []
		self.bins = None
		self.max = None
		self.label = None
	def __call__(self):
		if not self.bins:
			self.getBins()
		ax = self.fig.add_subplot(111)
		if self.points:
			ax.hist(self.points, bins=self.bins, color='red')
		ax.set_title(self.label)
		return self.createResponse()
	def getBins(self):
		if self.max==None:
			self.max = max(self.points)
		factor = 1
		while (self.max+2)/factor > 15:
			factor += 1
		self.bins = [i*factor-0.5 for i in range(int(math.ceil((self.max+2)/factor)))]

@view_config(route_name='exam_histogram_for_exercise', context=ExerciseContext, permission='statistics')
class HistogramForExercise(Histogram):
	def __init__(self, request):
		Histogram.__init__(self, request)
		self.label = u'Punkteverteilung diese Gruppe' if self.request.context.tutorials else u'Punkteverteilung alle Gruppen'
		self.exercise = self.request.context.exercise
		exercise_points = self.exercise.exercise_points
		students = self.exercise.exam.lecture.lecture_students_for_tutorials(tutorials=self.request.context.tutorials, order=False)
		exercise_points = exercise_points.filter(ExerciseStudent.student_id.in_([s.student_id for s in students]))
		self.points = [round(float(p.points)) for p in exercise_points if p.points!=None]
		self.max = self.exercise.maxpoints

@view_config(route_name='exam_histogram_for_exam', context=ExamContext, permission='statistics')
class HistogramForExam(Histogram):
	def __init__(self, request):
		Histogram.__init__(self, request)
		self.label = u'Punkteverteilung diese Gruppe' if self.request.context.tutorials else u'Punkteverteilung alle Gruppen'
		self.exam = self.request.context.exam
		students = self.exam.lecture.lecture_students_for_tutorials(tutorials=self.request.context.tutorials, order=False)
		exercise_points = self.exam.getResults(students=students)
		self.points = [round(float(p.points)-0.01) for p in exercise_points if p.points!=None]
		self.max = self.exam.getMaxpoints()

@view_config(route_name='exam_enter_points_single', renderer='muesli.web:templates/exam/enter_points_single.pt', context=ExamContext, permission='enter_points')
def enterPointsSingle(request):
	exam = request.context.exam
	exercises = exam.exercises
	request.javascript.add('prototype.js')
	request.javascript.add('scriptaculous/scriptaculous.js')
	show_tutor = not request.context.tutorials
	show_time = (not request.context.tutorials) or len(request.context.tutorials) > 1
	code = """
  var current_row_counter = 0;
  var currentrow = 0;

  function processkey(row,event) {
    if (event.keyCode == 13) {
      submit_points(row);
    } else {
    }
  }

  function student_selected() {
    if ($('student_hidden').value == '') {
      return;
    }
    var table = $('enter_points_table');
    var rows = table.rows.length;
    currentrow = rows;
    var tr = table.insertRow(rows);
    tr.id = 'row-'+rows;
    tr.onkeypress = function(event) {processkey(rows,event);};
"""
	if show_tutor:
		code += """
    var td_tutor = document.createElement('td');
    td_tutor.id = 'tutor-'+rows;
    tr.appendChild(td_tutor);
"""
	if show_time:
		code += """
    var td_time = document.createElement('td');
    td_time.id = 'time-'+rows;
    tr.appendChild(td_time);
"""
	if show_tutor or show_time:
		code += """
    var parameterHash = new Hash();
    parameterHash.set('student_id', $('student_hidden').value);
    new Ajax.Request('%s', {
        parameters: parameterHash,
        onComplete:function(transport){
""" % (request.route_path('tutorial_ajax_get_tutorial', lecture_id = request.context.exam.lecture_id))
		if show_tutor: code += """
          $('tutor-'+rows).innerHTML = transport.responseJSON['tutor'];
"""
		if show_time: code += """
          $('time-'+rows).innerHTML = transport.responseJSON['time'];
"""
		code += """
        }
      }
    );
"""
	code += """
    var td_student_name = document.createElement('td');
    var input_student_id = document.createElement('input');
    input_student_id.type = 'hidden';
    input_student_id.id = 'id-'+rows;
    input_student_id.value = $('student_hidden').value;
    td_student_name.innerHTML = $('student').value;
    td_student_name.appendChild(input_student_id);
    tr.appendChild(td_student_name);
    var td_exercise;
    var input_exercise;
"""
	for e in exercises:
		code += """
    td_exercise = document.createElement('td');
    tr.appendChild(td_exercise);
    input_exercise = document.createElement('input');
    td_exercise.appendChild(input_exercise);
    input_exercise.id = 'points-'+rows+'-%s';
    input_exercise.onchange = function(event) {update_total(rows)};
    input_exercise.className = 'points';
    input_exercise.size = 3;
""" % (e.id)
	code += """
    var td_sum = document.createElement('td');
    tr.appendChild(td_sum);
    var sum_input = document.createElement('input');
    sum_input.id = 'total-'+rows;
    sum_input.readOnly = true;
    sum_input.size=4;
    td_sum.appendChild(sum_input);
    var td_button = document.createElement('td');
    tr.appendChild(td_button);
    var button_save = document.createElement('input');
    button_save.id = 'button-save-'+rows;
    button_save.type = 'button';
    button_save.value = 'Abspeichern';
    button_save.onclick = function() {submit_points(rows);};
    td_button.appendChild(button_save);
    var button_correct = document.createElement('input');
    button_correct.id = 'button-correct-'+rows;
    button_correct.type = 'button';
    button_correct.value = 'Korrigieren';
    button_correct.onclick = function() {correct_points(rows);};
    button_correct.hide();
    td_button.appendChild(button_correct);
    var td_status = document.createElement('td');
    tr.appendChild(td_status);
    td_status.id = 'status-'+rows;
    var getParameterHash = new Hash();
    getParameterHash.set('student_id', $('student_hidden').value);
"""
	code += """
    new Ajax.Request('%s', {
""" % (request.route_path('exam_ajax_get_points', exam_id = exam.id, tutorial_ids = request.context.tutorial_ids_str))
	code += """
        parameters: getParameterHash,
        onComplete:function(transport){
"""
	for e in exercises:
		code += """
          if ($('points-'+rows+'-%s').value == '') {
            var value = transport.responseJSON['points']['%s'];
            if (value == null)
              value = '';
            $('points-'+rows+'-%s').value = value;
          }
""" % (e.id, e.id, e.id)
	code += """
          update_total(rows);
        }
      }
    );

    $('select_student_form').hide();
    $('points-'+rows+'-%s').focus();
  }
""" % (exercises[0].id)
	code += """

  function submit_points(row) {
    $('select_student_form').show();
    var parameterHash = new Hash();
    parameterHash.set('student_id', $('id-'+row).value);
    var current_input;
"""
	for e in exercises:
		code += """
    current_input = $('points-'+row+'-%s');
    parameterHash.set('points-%s', current_input.value);
    current_input.readOnly = true;
""" %(e.id, e.id)
	code += """
    $('button-save-'+row).hide();
    $('button-correct-'+row).show();
    $('status-'+row).innerHTML = 'saving...';
    new Ajax.Request('%s', {
        parameters: parameterHash,
        onSuccess:function(transport){
          $('status-'+row).innerHTML = transport.responseJSON['msg'];//'transmitted';
        },
        onFailure:function(transport){
          $('status-'+row).innerHTML = 'failed';
        }
      }
    );
    $('student_hidden').value = '';
    $('student').value = '';
    $('student').focus();
  }
""" % request.route_path('exam_ajax_save_points', exam_id = exam.id, tutorial_ids = request.context.tutorial_ids_str)
	code += """
  function correct_points(row) {
    $('button-correct-'+row).hide();
"""
	for e in exercises:
		code += """
    $('points-'+row+'-%s').readOnly = false;
""" % e.id
	code += """
    $('status-'+row).innerHTML = '';
    $('button-save-'+row).show();
  }
"""
	return {
		'code': code,
		'exam': exam,
		'exercises': exercises,
		'tutorial_ids': request.context.tutorial_ids_str,
		'show_tutor': show_tutor,
		'show_time': show_time
		}

@view_config(route_name='exam_ajax_save_points', renderer='json', context=ExamContext, permission='enter_points')
def ajaxSavePoints(request):
	exam = request.context.exam
	lecture_students = exam.lecture.lecture_students_for_tutorials(tutorials=request.context.tutorials)
	student_id = request.POST['student_id']
	student = lecture_students.filter(models.LectureStudent.student_id == student_id).one().student
	exercise_points = exam.exercise_points.filter(models.ExerciseStudent.student_id==student.id)
	d_points = {}
	json_data = {'msg': '', 'format_error_cells': []}
	for ep in exercise_points:
		d_points[ep.exercise_id] = ep
	for exercise in exam.exercises:
		if not exercise.id in d_points:
			ep = models.ExerciseStudent()
			ep.student = student
			ep.exercise = exercise
			request.db.add(ep)
			d_points[exercise.id] = ep
		get_param = 'points-%s' % exercise.id
		if get_param in request.POST:
			p = request.POST[get_param].replace(',','.')
			if p:
				try:
					p = float(p)
					d_points[exercise.id].points = p
				except ValueError:
					json_data['format_error'] = 1
					json_data['msg'] += "Invalid value '%s' for exercise '%s'. " % (p, exercise.id)
					json_data['format_error_cells'].append(exercise.id)
			else:
				if d_points[exercise.id] in request.db:
					#obj = d_points[exercise.id]
					#from sqlalchemy.orm import object_session
					#from sqlalchemy.orm.util import has_identity
					#if object_session(obj) is None and not has_identity(obj):
						#print "transient"
					#if object_session(obj) is not None and not has_identity(obj):
						#print "pending"
					#if object_session(obj) is None and has_identity(obj):
						#print "detached"
					#if object_session(obj) is not None and has_identity(obj):
						#print "persistent"
					try:
						request.db.delete(d_points[exercise.id])
						#print "deleted"
					except sqlalchemy.exc.InvalidRequestError:
						# Object not really added
						# Seems not to work really
						#print "not deleted"
						pass
	request.db.commit()
	json_data['msg'] = json_data['msg'] or 'sucessfull'
	return json_data

@view_config(route_name='exam_ajax_get_points', renderer='json', context=ExamContext, permission='view_points')
def ajaxGetPoints(request):
	exam = request.context.exam
	lecture_students = exam.lecture.lecture_students_for_tutorials(tutorials=request.context.tutorials)
	student_id = request.POST['student_id']
	student = lecture_students.filter(models.LectureStudent.student_id == student_id).one().student
	exercise_points = exam.exercise_points.filter(models.ExerciseStudent.student_id==student.id)
	points = {}
	json_data = {'msg': '', 'format_error_cells': []}
	for ep in exercise_points:
		points[ep.exercise_id] = float(ep.points) if ep.points else None
	return {'points': points}
