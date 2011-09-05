# muesli/models.py
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

# -*- coding: utf-8 -*-

import muesli

import sqlalchemy
import sqlalchemy.ext.declarative
from sqlalchemy import Column, ForeignKey, CheckConstraint, Text, Integer, Boolean, Unicode, DateTime, Date, Numeric, func, Table
from sqlalchemy.orm import relationship, sessionmaker
from muesli.types import *
Base = sqlalchemy.ext.declarative.declarative_base()

engine = muesli.engine()
Session = sessionmaker(bind=engine)

lecture_tutors_table = Table('lecture_tutors', Base.metadata,
	Column('lecture', Integer, ForeignKey('lectures.id'), primary_key=True),
	Column('tutor', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	email = Column(Text, unique=True, nullable=False)
	first_name = Column(Text, nullable=False)
	last_name = Column(Text, nullable=False)
	password = Column(Text)
	matrikel = Column(Text)
	birth_date = Column(Text)
	birth_place = Column(Text)
	subject = Column(Text)
	title = Column(Text)
	# TODO: Convert to boolean
	is_admin = Column(Integer, nullable=False, default=0)
	is_assistant = Column(Integer, nullable=False, default=0)

class Confirmation(Base):
	__tablename__ = 'confirmations'
	hash = Column(Unicode(length=40), primary_key=True)
	user_id = Column('user', Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
	user = relationship(User, backref='confirmations')
	source = Column(Text, nullable=False)
	what = Column(Text)
	created_on = Column(DateTime, nullable=False, default=func.CURRENT_TIMESTAMP)

class Lecture(Base):
	__tablename__ = 'lectures'
	id = Column(Integer, primary_key=True)
	assistant_id = Column('assistant', Integer, ForeignKey(User.id, ondelete='SET NULL'))
	assistant = relationship(User, backref='lectures_as_assistant')
	name = Column(Text)
	# lecture type
	#  'lecture'
	#  'seminar'
	type = Column(Text, nullable=False, default='lecture')
	# term
	#  Format: yyyyt
	#  where "yyyy" is the year the term starts and "t" is "1" for summer term
	#  and "2" for winter term
	term = Column(ColumnWrapper(Term)(length=5))
	# lecture id used in LSF.
	lsf_id = Column(Text)
	lecturer = Column(Text)
	url = Column(Text)
	password = Column(Text)
	is_visible = Column(Boolean, nullable=False, default=True)
	# tutorial subscription mode:
	#  'off'    - no subscription allowed
	#  'direct' - direct subscription to tutorials
	#  'prefs'  - preferences based subscription to tutorials
	#  'static' - no subscription, no unsubscription
	mode = Column(Text, nullable=False, default='off')
	minimum_preferences = Column(Integer, default=None)
	tutors = relationship(User, secondary=lecture_tutors_table, backref = "lectures_as_tutor")
#	@property
#	def tutors(self):
#		session = Session.object_session(self)
#		return session.query(User).filter(User.lecture_tutors.any(LectureTutor.lecture==self))

class Exam(Base):
	__tablename__ = 'exams'
	id = Column(Integer, primary_key=True)
	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id))
	lecture = relationship(Lecture, backref='exams')
	name = Column(Text)
	# exam type
	#  'exam'
	#  'assignment'
	#  'presence_assignment'
	#  'mock_exam'
	category = Column(Text, nullable=False)
	admission = Column(Boolean)
	registration = Column(Boolean)
	url = Column(Text)

class Tutorial(Base):
	__tablename__ = 'tutorials'
	id = Column(Integer, primary_key=True)
	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id))
	lecture = relationship(Lecture, backref='tutorials')
	tutor_id = Column('tutor', Integer, ForeignKey(User.id))
	tutor = relationship(User, backref='tutorials_as_tutor')
	place = Column(Text)
	max_students = Column(Integer, nullable=False, default=0)
	comment = Column(Text)
	@property
	def students(self):
		session = Session.object_session(self)
		return session.query(User).filter(User.lecture_students.any(LectureStudent.tutorial==self))
	# weekday and time of tutorial
	# format: "D HH:MM"
	# where
	#   D - day: 0..6, where 0 is Monday
	#  HH - hour
	#  MM - minute
	time = Column(ColumnWrapper(TutorialTime)(length=7))
	date = Column(Date)
	is_special = Column(Boolean, nullable=False, default=False)

class TimePreference(Base):
	__tablename__ = 'time_preferences'
	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
	lecture = relationship(Lecture, backref='time_preferences')
	student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
	student = relationship(User, backref='time_preferences')
	time = Column(Unicode(length=7), primary_key=True)
	penalty = Column(Integer)

class TutorialPreference(Base):
	__tablename__ = 'tutorial_preferences'
	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
	lecture = relationship(Lecture, backref='tutorial_preferences')
	student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
	student = relationship(User, backref='tutorial_preferences')
	tutorial_id = Column('tutorial', Integer, ForeignKey(Tutorial.id), primary_key=True)
	tutorial = relationship(Tutorial, backref='tutorial_preferences')
	penalty = Column(Integer)

class LectureStudent(Base):
	__tablename__ = 'lecture_students'
	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
	lecture = relationship(Lecture, backref='lecture_students')
	student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
	student = relationship(User, backref='lecture_students')
	tutorial_id = Column('tutorial', Integer, ForeignKey(Tutorial.id))
	tutorial = relationship(Tutorial, backref='lecture_students')

class LectureRemovedStudent(Base):
	__tablename__ = 'lecture_removed_students'
	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
	lecture = relationship(Lecture, backref='lecture_removed_students')
	student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
	student = relationship(User, backref='lecture_removed_students')
	tutorial_id = Column('tutorial', Integer, ForeignKey(Tutorial.id))
	tutorial = relationship(Tutorial, backref='lecture_removed_students')

#class LectureTutor(Base):
#	__tablename__ = 'lecture_tutors'
#	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
#	lecture = relationship(Lecture, backref='lecture_tutors')
#	tutor_id = Column('tutor', Integer, ForeignKey(User.id), primary_key=True)
#	tutor = relationship(User, backref='lecture_tutors')

class Exercise(Base):
	__tablename__ = 'exercises'
	id = Column(Integer, primary_key=True)
	exam_id = Column('exam', Integer, ForeignKey(Exam.id))
	exam = relationship(Exam, backref='exercises')
	nr = Column(Integer, nullable=False)
	maxpoints = Column(Numeric(precision=8, scale=1), nullable=False)

class ExerciseStudent(Base):
	__tablename__ = 'exercise_students'
	exercise_id = Column('exercise', Integer, ForeignKey(Exercise.id), primary_key=True)
	exercise = relationship(Exercise, backref='exercise_points')
	student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
	student = relationship(User, backref='exercise_points')
	points = Column(Numeric(precision=8, scale=1))

class ExamAdmission(Base):
	__tablename__ = 'exam_admissions'
	exam_id = Column('exam', Integer, ForeignKey(Exam.id), primary_key=True)
	exam = relationship(Exam, backref='exam_admissions')
	student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
	student = relationship(User, backref='exam_admissions')
	admission = Column(Boolean)
	registration = Column(Boolean)

class Grading(Base):
	__tablename__ = 'gradings'
	id = Column(Integer, primary_key=True)
	lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), nullable=False, primary_key=True)
	lecture = relationship(Lecture, backref='gradings')
	name = Column(Text)
	formula = Column(Text)
	# "termin" as defined in HISPOS:
	# 01 Haupttermin
	# 02 Nachtermin
	hispos_type = Column(Text)
	hispos_date = Column(Text)
	examiner_id = Column(Text)

class StudentGrade(Base):
	__tablename__ = 'student_grades'
	grading_id = Column('grading', Integer, ForeignKey(Grading.id), nullable=False, primary_key=True)
	grading = relationship(Grading, backref='student_grades')
	student_id = Column('student', Integer, ForeignKey(User.id), nullable=False, primary_key=True)
	student = relationship(User, backref='student_grades')
	grade = Column(Numeric(precision=2, scale=1), CheckConstraint('grade >= 1.0 AND grade <= 5.0'))
  
class GradingExam(Base):
	__tablename__ = 'grading_exams'
	grading_id = Column('grading', Integer, ForeignKey(Grading.id, ondelete='CASCADE'), nullable=False, primary_key=True)
	grading = relationship(Grading, backref='grading_exams')
	exam_id = Column('exam', Integer, ForeignKey(Exam.id, ondelete='CASCADE'), nullable=False, primary_key=True)
	exam = relationship(Exam, backref='grading_exams')
