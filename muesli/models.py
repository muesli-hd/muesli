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

import math
import random
import time
import hashlib

import sqlalchemy
import sqlalchemy as sa
import sqlalchemy.ext.declarative
from sqlalchemy import Column, ForeignKey, CheckConstraint, Text, String, Integer, Boolean, Unicode, DateTime, Date, Numeric, func, Table, text
from sqlalchemy.orm import relationship, backref, column_property, object_session
from muesli.types import Term, TutorialTime, ColumnWrapper
from muesli.utils import DictOfObjects, AutoVivification, editOwnTutorials, listStrings, getTerms
from muesli.web.api.v1 import allowed_attributes

from marshmallow import Schema, fields, pre_load, post_load
from marshmallow.exceptions import ValidationError


Base = sqlalchemy.ext.declarative.declarative_base()


lecture_tutors_table = Table('lecture_tutors', Base.metadata,
        Column('lecture', Integer, ForeignKey('lectures.id'), primary_key=True),
        Column('tutor', Integer, ForeignKey('users.id'), primary_key=True)
)

grading_exam_table = Table('grading_exams', Base.metadata,
        Column('grading', Integer, ForeignKey('gradings.id', ondelete='CASCADE'), nullable=False, primary_key=True),
        Column('exam', Integer, ForeignKey('exams.id', ondelete='CASCADE'), nullable=False, primary_key=True)
)

lecture_assistants_table = Table('lecture_assistants', Base.metadata,
        Column('lecture', Integer, ForeignKey('lectures.id', ondelete='CASCADE'), nullable=False, primary_key=True),
        Column('assistant', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, primary_key=True)
)

# class GradingExam(Base):
#        __tablename__ = 'grading_exams'
#        grading_id = Column('grading', Integer, ForeignKey(Grading.id, ondelete='CASCADE'), nullable=False, primary_key=True)
#        grading = relationship(Grading, backref='grading_exams')
#        exam_id = Column('exam', Integer, ForeignKey(Exam.id, ondelete='CASCADE'), nullable=False, primary_key=True)
#        exam = relationship(Exam, backref='grading_exams')


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    password = Column(Text)
    matrikel = Column(Text)
    subject = Column(Text)
    second_subject = Column(Text)
    title = Column(Text)
    # TODO: Convert to boolean
    is_admin = Column(Integer, nullable=False, default=0)
    is_assistant = Column(Integer, nullable=False, default=0)

    @property
    def name(self):
        name = "{}{}{}".format(
            self.title+' ' if self.title is not None else '',
            self.first_name+' ' if self.first_name is not None else '',
            self.last_name if self.last_name is not None else ''
        )
        return name

    @property
    def tutorials(self):
        session = object_session(self)
        return session.query(Tutorial).filter(Tutorial.lecture_students.any(LectureStudent.student_id == self.id)).join(Tutorial.lecture).order_by(Lecture.term)

    @property
    def tutorials_as_tutor(self):
        session = object_session(self)
        return session.query(Tutorial).filter(Tutorial.tutor_id == self.id).join(Tutorial.lecture).order_by(Lecture.term,Lecture.name,Tutorial.time)

    @property
    def tutorials_removed(self):
        session = object_session(self)
        return session.query(LectureRemovedStudent).filter(LectureRemovedStudent.student_id == self.id).join(LectureRemovedStudent.tutorial).join(Tutorial.lecture).order_by(Lecture.term,Lecture.name,Tutorial.time)

    def prepareMultiTutorials(self):
        mt = {}
        for tutorial in self.tutorials_as_tutor:
            if tutorial.lecture.id in mt:
                mt[tutorial.lecture.id].append(tutorial)
            else:
                mt[tutorial.lecture.id] = [tutorial]
        return mt

    def getFirstName(self):
        return self.first_name

    def getLastName(self):
        return self.last_name

    def prepareTimePreferences(self):
        time_preferences = self.time_preferences
        tps = {}
        for tp in time_preferences:
            if tp.lecture.mode == 'prefs':
                if tp.lecture.id in tps:
                    tps[tp.lecture.id].append(tp)
                else:
                    tps[tp.lecture.id] = [tp]
        return tps

    def hasPreferences(self, lecture=None):
        session = object_session(self)
        query = session.query(TimePreference).filter(TimePreference.student_id == self.id)
        if lecture:
            query = query.filter(TimePreference.lecture_id == lecture.id)
        return query.count() > 0

    def confirmed(self):
        return self.password != None

    def formatCompleteSubject(self):
        ret = self.subject
        if self.second_subject:
            ret += ', Zweites Hauptfach: %s' % self.second_subject
        return ret

    def is_deletable(self):
        if (self.tutorials.all()):
            return False
        elif self.tutorials_as_tutor.all():
            return False
        elif self.lectures_as_tutor:
            return False
        elif self.lectures_as_assistant.all():
            return False
        elif len(self.exercise_points) > 0:
            return False
        elif len(self.student_grades.all()) > 0:
            return False
        elif len(self.tutorials_removed.all()) > 0:
            return False
        return True

    def __str__(self):
        return '{name} <{email}>'.format(name=self.name, email=self.email)

    def __repr__(self):
        return 'u<User %r <%r>>' % (self.name, self.email)


class Confirmation(Base):
    __tablename__ = 'confirmations'
    hash = Column(Unicode(length=40), primary_key=True)
    user_id = Column('user', Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    user = relationship(User, backref='confirmations')
    source = Column(Text, nullable=False)
    what = Column(Text)
    created_on = Column(DateTime, nullable=False, default=text('CURRENT_TIMESTAMP'))

    def __init__(self):
        self.hash = hashlib.sha1(bytes("%s-%s" % (time.time(), random.random()), "utf-8")).hexdigest()


class Lecture(Base):
    __tablename__ = 'lectures'
    id = Column(Integer, primary_key=True)
    # Should be removed some day. Stays here just to make muesli3 work.
    assistant_id = Column('assistant', Integer, ForeignKey(User.id, ondelete='SET NULL'))
    old_assistant = relationship(
        User, backref=backref(
            'lectures_as_assistant_old', order_by='Lecture.term', lazy='select'
        )
    )
    assistants = relationship(
        User, secondary=lecture_assistants_table, backref=backref(
            "lectures_as_assistant", order_by='Lecture.term', lazy='dynamic'
        )
    )
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
    tutor_rights = Column(Text, nullable=False, default=editOwnTutorials)
    tutors = relationship(User, secondary=lecture_tutors_table, backref="lectures_as_tutor")

    @property
    def students(self):
        session = object_session(self)
        return session.query(User).filter(User.lecture_students.any(LectureStudent.lecture_id==self.id))

    def lecture_students_for_tutorials(self, tutorials=[], order=True):
        ls = self.lecture_students
        if order:
            ls = ls.join(LectureStudent.student).order_by(User.last_name, User.first_name)
        if tutorials:
            ls = ls.filter(LectureStudent.tutorial_id.in_([tut.id for tut in tutorials]))  # sqlalchemy.or_(*[LectureStudent.tutorial_id==tut.id for tut in tutorials]))
        return ls
#       @property
#       def tutors(self):
#               session = object_session(self)
#               return session.query(User).filter(User.lecture_tutors.any(LectureTutor.lecture==self))

    def prepareTimePreferences(self, user=None):
        session = object_session(self)
        if self.mode == "prefs":
            times = session.query(sqlalchemy.func.sum(Tutorial.max_students), Tutorial.time).\
                    filter(Tutorial.lecture == self).\
                    group_by(Tutorial.time)
            times = [{'weekday':   result[1].weekday(),
                      'timeofday': result[1].time(),
                      'time':      result[1],
                      'max_students': result[0]} for result in times]
            for time in times:
                if user:
                    pref = session.query(TimePreference).get((self.id, user.id, time['time'].value))
                    if not pref:
                        time['penalty'] = 100
                    else:
                        time['penalty'] = pref.penalty
                else:
                    time['penalty'] = 100
            if user:
                if session.new or session.dirty or session.deleted:
                    session.commit()
        else:
            times = []
        return times

    def pref_subjects(self):
        session = object_session(self)
        return session.query(sqlalchemy.func.count(User.id), User.subject).\
                filter(User.time_preferences.any(TimePreference.lecture_id == self.id)).\
                group_by(User.subject).order_by(User.subject)

    def subjects(self):
        session = object_session(self)
        return session.query(sqlalchemy.func.count(User.id), User.subject).\
                filter(User.lecture_students.any(LectureStudent.lecture_id == self.id)).\
                group_by(User.subject).order_by(User.subject)

    def getLectureResults(self, tutorials=[], students=None):
        session = object_session(self)
        if not students:
            students = self.lecture_students_for_tutorials(tutorials)
        exercises = session.query(Exercise).filter(Exercise.exam_id.in_([e.id for e in self.exams])).all()
        lecture_results = session.query(\
                        sqlalchemy.func.sum(ExerciseStudent.points).label('points'),
                        ExerciseStudent.student_id.label('student_id'),
                        Exam, Exam.id)\
                        .filter(ExerciseStudent.exercise_id.in_([e.id  for e in exercises]))\
                        .filter(ExerciseStudent.student_id.in_([s.student_id for s in students]))\
                        .join(Exercise, ExerciseStudent.exercise).join(Exam, Exercise.exam)\
                        .group_by(ExerciseStudent.student_id, Exam)
        return lecture_results

    def getLectureResultsByCategory(self, *args, **kwargs):
        session = object_session(self)
        results = self.getLectureResults(*args, **kwargs).subquery()
        return session.query(func.sum(results.c.points).label('points'), results.c.student_id, results.c.category)\
                .group_by(results.c.category, results.c.student_id)

    def getPreparedLectureResults(self, lecture_results):
        results = AutoVivification()
        for res in lecture_results:
            results[res.student_id][res.Exam.id] = res.points
        for exam in self.exams:
            for student_results in list(results.values()):
                student_results[exam.category] = student_results.get(exam.category,0)+(student_results.get(exam.id,0) or 0)
        return results

    def getGradingResults(self, tutorials=[], students=None):
        session = object_session(self)
        return session.query(StudentGrade).filter(StudentGrade.grading_id.in_([g.id for g in self.gradings]))


class Exam(Base):
    __tablename__ = 'exams'
    id = Column(Integer, primary_key=True)
    lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id))
    lecture = relationship(Lecture, backref=backref('exams', lazy='dynamic', order_by='Exam.name'))
    name = Column(Text)
    # exam type
    #  'exam'
    #  'assignment'
    #  'practical assignment'
    #  'presence_assignment'
    #  'mock_exam'
    category = Column(Text, nullable=False)
    admission = Column(Boolean)
    registration = Column(Boolean)
    medical_certificate = Column(Boolean)
    url = Column(Text)
    results_hidden = Column(Boolean, default=False)

    @property
    def exercise_points(self):
        session = object_session(self)
        return session.query(ExerciseStudent).filter(ExerciseStudent.exercise.has(Exercise.exam_id==self.id))

    def getResults(self, students=None):
        session = object_session(self)
        pointsQuery = self.exercise_points
        if students:
            pointsQuery = pointsQuery.filter(ExerciseStudent.student_id.in_([s.student_id for s  in students]))
        pointsStmt = pointsQuery.subquery()
        examPoints = session.query(\
                        pointsStmt.c.student.label('student_id'),
                        func.sum(pointsStmt.c.points).label('points'),
                ).group_by(pointsStmt.c.student)
        return examPoints

    def getResultsForStudent(self, student):
        session = object_session(self)
        pointsQuery = self.exercise_points
        pointsQuery = pointsQuery.filter(ExerciseStudent.student_id==student.id)
        results = {}
        for points in pointsQuery.all():
            results[points.exercise_id] = {'points': points.points,
                                           'exercise': points.exercise}
        nonNullPoints = [x for x in [r['points'] for r in results.values()] if x]
        if nonNullPoints:
            results['sum'] = sum(nonNullPoints)
        else:
            results['sum'] = None
        for e in self.exercises:
            if e.id not in results:
                results[e.id] = {'points': None, 'exercise': e}
        return results

    def getStatistics(self, tutorials=None, students=None, statistics=None, prefix='lec'):
        if statistics is None:
            statistics = AutoVivification()
        session = object_session(self)
        if not students:
            students = self.lecture.lecture_students_for_tutorials(tutorials).all()
        pointsQuery = self.exercise_points.filter(ExerciseStudent.student_id.in_([s.student_id for s  in students]))\
                                                .filter(ExerciseStudent.points!=None)
        pointsStmt = pointsQuery.subquery()
        exerciseStatistics = session.query(\
                        pointsStmt.c.exercise.label('exercise_id'),
                        func.count(pointsStmt.c.student).label('count'),
                        func.avg(pointsStmt.c.points).label('avg'),
                        func.variance(pointsStmt.c.points).label('variance')
                ).group_by(pointsStmt.c.exercise)
        examPoints = session.query(\
                        pointsStmt.c.student.label('student_id'),
                        func.sum(pointsStmt.c.points).label('points'),
                ).group_by(pointsStmt.c.student).subquery()
        examStatistics = session.query(\
                        func.count(examPoints.c.student_id).label('count'),
                        func.avg(examPoints.c.points).label('avg'),
                        func.variance(examPoints.c.points).label('variance'),
                ).one()
        statistics['exam'] = {
                prefix+'_avg': examStatistics.avg,
                prefix+'_std': math.sqrt(examStatistics.variance) if examStatistics.variance else None,
                prefix+'_count': examStatistics.count,
                'max': self.getMaxpoints()}
        for e in self.exercises:
            statistics[e.id] = {prefix+'_avg': None, prefix+'_std': None, prefix+'_count': 0, 'max': e.maxpoints}
        for e in exerciseStatistics.all():
            statistics[e.exercise_id] = {
                    prefix+'_avg': e.avg,
                    prefix+'_std': math.sqrt(e.variance) if e.variance else None,
                    prefix+'_count': e.count
                    }
        return statistics

    def getStatisticsBySubjects(self, tutorials=None, students=None, statistics=None, prefix='lec'):
        session = object_session(self)
        if not students:
            students = self.lecture.lecture_students_for_tutorials(tutorials)
        exercise_points = session.query(ExerciseStudent, ExerciseStudent.student)
        pointsQuery = self.exercise_points.filter(ExerciseStudent.student_id.in_([s.student_id for s  in students]))\
                .filter(ExerciseStudent.exercise_id.in_([e.id for e in self.exercises]))\
                .filter(ExerciseStudent.points!=None).subquery()
        pointsStmt = session.query(User.subject, pointsQuery).join(pointsQuery, pointsQuery.c.student==User.id).subquery()
        exerciseStatistics = session.query(\
                        pointsStmt.c.exercise.label('exercise_id'),
                        pointsStmt.c.subject.label('subject'),
                        func.count(pointsStmt.c.student).label('count'),
                        func.avg(pointsStmt.c.points).label('avg'),
                        func.variance(pointsStmt.c.points).label('variance')
                ).group_by(pointsStmt.c.exercise, pointsStmt.c.subject).all()
        examPoints = session.query(\
                        pointsStmt.c.student.label('student_id'),
                        pointsStmt.c.subject.label('subject'),
                        func.sum(pointsStmt.c.points).label('points'),
                ).group_by(pointsStmt.c.student, pointsStmt.c.subject).subquery()
        examStatistics = session.query(\
                        examPoints.c.subject.label('subject'),
                        func.count(examPoints.c.student_id).label('count'),
                        func.avg(examPoints.c.points).label('avg'),
                        func.variance(examPoints.c.points).label('variance'),
                ).group_by(examPoints.c.subject).all()
        if statistics is None:
            statistics = AutoVivification()
        maxpoints = self.getMaxpoints()
        for res in examStatistics:
            statistics[res.subject]['exam'] = {prefix+'_avg': res.avg,
                                               prefix+'_std': math.sqrt(res.variance) if res.variance else None,
                                               prefix+'_count': res.count,
                                               'max': maxpoints}
        for e in exerciseStatistics:
            statistics[e.subject][e.exercise_id] = {
                    prefix+'_avg': e.avg,
                    prefix+'_std': math.sqrt(e.variance) if e.variance else None,
                    prefix+'_count': e.count,
                    'max': session.query(Exercise).get(e.exercise_id).maxpoints
                    }
        return statistics

    def getMaxpoints(self):
        return int(sum([e.maxpoints for e in self.exercises]))

    def getQuantils(self, students=None):
        results = self.getResults(students=students).all()
        allcount = len([res for res in results if res.points and res.points >= 0])
        quantils = []
        for i in range(self.getMaxpoints()+1):
            count = len([res for res in results if res.points and res.points >= i])
            quantils.append({
                    'min_points': i,
                    'min_percent': i/float(self.getMaxpoints()) if self.getMaxpoints() else 0,
                    'count': count,
                    'quantile': float(count)/allcount if allcount!=0 else 0})
        return quantils

    @property
    def admissions_string(self):
        l = []
        if self.admission:
            l.append('Zulassung')
        if self.registration:
            l.append('Anmeldung')
        if self.medical_certificate:
            l.append('Attest')
        return listStrings(l)


class Tutorial(Base):
    __tablename__ = 'tutorials'
    id = Column(Integer, primary_key=True)
    lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id))
    lecture = relationship(Lecture, lazy='joined',
                           backref=backref('tutorials', order_by='Tutorial.time,Tutorial.comment', lazy='select'))
    tutor_id = Column('tutor', Integer, ForeignKey(User.id))
    tutor = relationship(User, lazy='joined')
    place = Column(Text)
    max_students = Column(Integer, nullable=False, default=0)
    comment = Column(Text)
    video_call = Column(Text)

    @property
    def students(self):
        session = object_session(self)
        return session.query(User).filter(User.lecture_students.any(LectureStudent.tutorial==self))

    @property
    def tutor_name(self):
        if self.tutor:
            return self.tutor.last_name
        else:
            return '-'
    # weekday and time of tutorial
    # format: "D HH:MM"
    # where
    #   D - day: 0..6, where 0 is Monday
    #  HH - hour
    #  MM - minute
    time = Column(ColumnWrapper(TutorialTime)(length=7))
    date = Column(Date)
    is_special = Column(Boolean, nullable=False, default=False)
    # student_count defined below, after LectureStudent is defined


class TimePreference(Base):
    __tablename__ = 'time_preferences'
    lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
    lecture = relationship(Lecture, backref=backref('time_preferences', lazy='dynamic'))
    student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
    student = relationship(User, backref='time_preferences')
    time = Column(ColumnWrapper(TutorialTime)(length=7), primary_key=True)
    penalty = Column(Integer)


class LectureStudent(Base):
    __tablename__ = 'lecture_students'
    lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
    lecture = relationship(Lecture, backref=backref('lecture_students', lazy='dynamic'))
    student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
    student = relationship(User, backref=backref('lecture_students', lazy='dynamic'))
    tutorial_id = Column('tutorial', Integer, ForeignKey(Tutorial.id))
    tutorial = relationship(Tutorial, backref='lecture_students')

Tutorial.student_count = column_property(
                sa.select([sa.func.count(LectureStudent.student_id)]).\
                        where(LectureStudent.tutorial_id==Tutorial.id).scalar_subquery(),
                deferred=True
                )


class LectureRemovedStudent(Base):
    __tablename__ = 'lecture_removed_students'
    lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
    lecture = relationship(Lecture, backref=backref('lecture_removed_students', lazy='dynamic'))
    student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
    student = relationship(User, backref=backref('lecture_removed_students', lazy='dynamic'))
    tutorial_id = Column('tutorial', Integer, ForeignKey(Tutorial.id))
    tutorial = relationship(Tutorial, backref='lecture_removed_students')

# class LectureTutor(Base):
#        __tablename__ = 'lecture_tutors'
#        lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), primary_key=True)
#        lecture = relationship(Lecture, backref='lecture_tutors')
#        tutor_id = Column('tutor', Integer, ForeignKey(User.id), primary_key=True)
#        tutor = relationship(User, backref='lecture_tutors')


class Exercise(Base):
    __tablename__ = 'exercises'
    id = Column(Integer, primary_key=True)
    exam_id = Column('exam', Integer, ForeignKey(Exam.id))
    exam = relationship(Exam, backref=backref('exercises', order_by='Exercise.nr'))
    nr = Column(Integer, nullable=False)
    maxpoints = Column(Numeric(precision=8, scale=1), nullable=False)


class ExerciseStudent(Base):
    __tablename__ = 'exercise_students'
    exercise_id = Column('exercise', Integer, ForeignKey(Exercise.id), primary_key=True)
    exercise = relationship(Exercise, backref=backref('exercise_points', lazy='dynamic'))
    student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
    student = relationship(User, backref='exercise_points')
    points = Column(Numeric(precision=8, scale=1))


class ExamAdmission(Base):
    __tablename__ = 'exam_admissions'
    exam_id = Column('exam', Integer, ForeignKey(Exam.id), primary_key=True)
    exam = relationship(Exam, backref=backref('exam_admissions', lazy='dynamic'))
    student_id = Column('student', Integer, ForeignKey(User.id), primary_key=True)
    student = relationship(User, backref='exam_admissions')
    admission = Column(Boolean)
    registration = Column(Boolean)
    medical_certificate = Column(Boolean)


class Grading(Base):
    __tablename__ = 'gradings'
    id = Column(Integer, primary_key=True)
    lecture_id = Column('lecture', Integer, ForeignKey(Lecture.id), nullable=False)
    lecture = relationship(Lecture, backref='gradings')
    name = Column(Text)
    formula = Column(Text)
    # "termin" as defined in HISPOS:
    # 01 Haupttermin
    # 02 Nachtermin
    hispos_type = Column(Text)
    hispos_date = Column(Text)
    examiner_id = Column(Text)
    exams = relationship(Exam, secondary=grading_exam_table, backref = "gradings", order_by=Exam.id)


class StudentGrade(Base):
    __tablename__ = 'student_grades'
    grading_id = Column('grading', Integer, ForeignKey(Grading.id), nullable=False, primary_key=True)
    grading = relationship(Grading, backref=backref('student_grades', lazy='dynamic'))
    student_id = Column('student', Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    student = relationship(User, backref=backref('student_grades', lazy='dynamic'))
    grade = Column(Numeric(precision=2, scale=1), CheckConstraint('grade >= 1.0 AND grade <= 5.0'))

class EmailPreferences(Base):
    __tablename__ = 'email_preferences'
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    lecture_id = Column(Integer, ForeignKey(Lecture.id), nullable=False, primary_key=True)
    receive_status_mails = Column(Boolean, nullable=False)
    def __init__(self, user_id, lecture_id, receive_status_mails):
        self.user_id = user_id
        self.lecture_id = lecture_id
        self.receive_status_mails = receive_status_mails

class UserHasUpdated(Base):
    __tablename__ = 'user_has_updated'
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, primary_key=True)
    has_updated_info = Column(String, nullable=False)
    def __init__(self, user_id, user_has_updated):
        self.user_id = user_id
        self.has_updated_info = user_has_updated


# Marshmallow Schemas for Serializing and Deserializing Models
# Only relevant for the Api


class UserSchema(Schema):
    id = fields.Integer(dump_only=True)
    email = fields.Email()
    first_name = fields.String()
    last_name = fields.String()
    title = fields.String()
    matrikel = fields.String()
    subject = fields.String()

    @post_load()
    def get_user(self, data, many=False, partial=False):
        # See Issue #144 and linked PRs:
        # We just ignore the Values of many and partial as we do not (yet)
        # implement any specific behaviour there

        usr = self.context['session'].query(User).filter(User.email == data["email"]).one()
        if usr is None:
            raise ValidationError("User not found")
        return usr


class AssistantSchema(UserSchema):
    @post_load()
    def get_user(self, data, many=False, partial=False):
        # See Issue #144 and linked PRs:
        # We just ignore the Values of many and partial as we do not (yet)
        # implement any specific behaviour there

        usr = self.context['session'].query(User).filter(User.email == data["email"]).one()
        if usr is None or not usr.is_assistant:
            raise ValidationError("User not found or is not assistant")
        return usr


class ExamSchema(Schema):
    id = fields.Integer(dump_only=True)
    lecture_id = fields.Integer(dump_only=True)
    name = fields.String()
    category = fields.String()
    admission = fields.Boolean()
    registration = fields.Boolean()
    url = fields.Url()


class TutorialSchema(Schema):
    id = fields.Integer(dump_only=True)
    lecture_id = fields.Integer(required=True)
    place = fields.String(required=True)
    time = fields.Method("get_time", deserialize="load_time")
    max_students = fields.Integer(required=True)
    tutor = fields.Nested(
        UserSchema, only=allowed_attributes.user(), dump_only=True)
    comment = fields.String()
    students = fields.Nested(UserSchema, many=True, only=allowed_attributes.user(),dump_only=True)
    exams = fields.Nested(ExamSchema, many=True, only=["id", "name"], dump_only=True)
    student_count = fields.Method("get_student_num")

    def get_time(self, obj):
        return obj.time.__html__()

    def load_time(self, value):
        return TutorialTime(str(value))

    def get_student_num(self, obj):
        return obj.students.count()


class LectureSchema(Schema):
    id = fields.Integer(dump_only=True)
    assistants = fields.Nested(AssistantSchema, required=True, many=True, only=allowed_attributes.user())
    name = fields.String(required=True)
    type = fields.String()
    term = fields.Method("get_term", deserialize="load_term")
    lsf_id = fields.String()
    lecturer = fields.String()
    url = fields.Url()
    password = fields.String()
    is_visible = fields.Boolean()
    tutorials = fields.Nested(TutorialSchema, many=True, only=allowed_attributes.tutorial())
    tutors = fields.Nested(UserSchema, many=True, dump_only=True)

    # Converts the Muesli defined type Term to it's string representation
    def get_term(self, obj):
        return obj.term.__html__()

    # Constructs a Term from input like 20181
    def load_term(self, value):
        term = [Term(str(value)), Term(str(value))]
        if term in getTerms():
            return term[0]


class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    exam_id = fields.Integer()
    nr = fields.Integer()
    maxpoints = fields.Float()
    students = fields.Nested(UserSchema, only=allowed_attributes.user(), many=True)


class ExerciseStudentSchema(Schema):
    student = fields.Nested(UserSchema, only=allowed_attributes.user())
    points = fields.Float()


class BearerToken(Base):
    __tablename__ = 'bearertokens'
    id = Column(Integer, primary_key=True)
    client = Column(Text)
    user_id = Column(ForeignKey(User.id))
    user = relationship(User)
    scopes = Column(Text)
    access_token = Column(String(100), unique=True)
    refresh_token = Column(String(100), unique=True)
    expires = Column(DateTime)
    description = Column(Text)
    revoked = Column(Boolean, default=False)
