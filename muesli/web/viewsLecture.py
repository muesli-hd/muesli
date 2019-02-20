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
from muesli.allocation import Allocation
from muesli.mail import Message, sendMail
from muesli.web.viewsExam import MatplotlibView

from collections import defaultdict

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound, HTTPForbidden
from pyramid.url import route_url

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc
import sqlalchemy
#
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.writer.excel import save_virtual_workbook
import io
#
from muesli import types

import re
import os

import yaml

@view_config(route_name='lecture_list', renderer='muesli.web:templates/lecture/list.pt')
class List:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
    def is_ana_or_la(self, lecture):
        name = lecture.name.lower()
        if any([name.startswith(start) for start in ['lineare algebra i', 'analysis i','lineare algebra 1', 'analysis 1']]):
            return True
        else:
            return False
    def __call__(self):
        lectures = self.db.query(models.Lecture).order_by(desc(models.Lecture.term), models.Lecture.name).options(joinedload(models.Lecture.assistants))
        if self.request.GET.get('show_all', '0')=='0':
            lectures = lectures.filter(models.Lecture.is_visible == True)
        lectures = lectures.all()
        sticky_lectures = []
        if lectures:
            newest_term = lectures[0].term
            sticky_lectures = [l for l in lectures if l.term == newest_term and self.is_ana_or_la(l)]
            lectures = [l for l in lectures if not l in sticky_lectures]
        return {'lectures': lectures,
                'sticky_lectures': sticky_lectures}

@view_config(route_name='lecture_view', renderer='muesli.web:templates/lecture/view.pt', context=LectureContext, permission='view')
class View:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
    def __call__(self):
        lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count')).get(self.lecture_id)
        times = lecture.prepareTimePreferences(user=self.request.user)
        subscribed = self.request.user.id in [s.id for s in lecture.students]
        return {'lecture': lecture,
                'subscribed': subscribed,
                'times': times,
                'prefs': utils.preferences}

@view_config(route_name='lecture_add_exam', renderer='muesli.web:templates/lecture/add_exam.pt', context=LectureContext, permission='edit')
class AddExam:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
    def __call__(self):
        lecture = self.db.query(models.Lecture).get(self.lecture_id)
        form = LectureAddExam(self.request)
        if self.request.method == 'POST' and form.processPostData(self.request.POST):
            exam = models.Exam()
            exam.lecture = lecture
            form.obj = exam
            form.saveValues()
            self.request.db.commit()
            form.message = "Neues Testat angelegt."
            return HTTPFound(location=self.request.route_url('exam_edit', exam_id = exam.id))
        return {'lecture': lecture,
                'form': form
               }

@view_config(route_name='lecture_add_tutor', context=LectureContext, permission='add_tutor')
def addTutor(request):
    lecture = request.context.lecture
    if request.method == 'POST':
        password = request.POST['password']
        if lecture.password and lecture.password == password:
            if request.user in lecture.tutors:
                request.session.flash('Sie sind bereits als Übungsleiter für diese Vorlesung eingetragen.', queue='messages')
            else:
                lecture.tutors.append(request.user)
                request.db.commit()
                request.session.flash('Sie wurden als Übungsleiter für diese Vorlesung eingetragen', queue='messages')
        else:
            request.session.flash('Bei der Anmeldung als Übungsleiter ist ein Fehler aufgetreten. Möglicherweise haben Sie ein falsches Passwort eingegeben oder die Anmeldung als Übungsleiter ist nicht mehr notwendig.', queue='errors')
    else:
        raise ValueError('lecture_add_tutor can only be called by POST-requests!')
    return HTTPFound(location=request.route_url('lecture_view', lecture_id = lecture.id))

@view_config(route_name='lecture_add_grading', renderer='muesli.web:templates/lecture/add_grading.pt', context=LectureContext, permission='edit')
class AddGrading:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
    def __call__(self):
        lecture = self.db.query(models.Lecture).get(self.lecture_id)
        form = LectureAddGrading(self.request)
        if self.request.method == 'POST' and form.processPostData(self.request.POST):
            grading = models.Grading()
            grading.lecture = lecture
            form.obj = grading
            form.saveValues()
            self.request.db.commit()
            form.message = "Neue Benotung angelegt."
        return {'lecture': lecture,
                'form': form
               }

@view_config(route_name='lecture_add_student', renderer='muesli.web:templates/lecture/add_student.pt', context=LectureContext, permission='edit')
class AddStudent:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
    def __call__(self):
        lecture = self.db.query(models.Lecture).get(self.lecture_id)
        tutorials = lecture.tutorials
        if self.request.method == 'POST':
            student_email = self.request.POST['student_email']
            new_tutorial  = int(self.request.POST['new_tutorial'])
            try:
                student = self.db.query(models.User).filter(models.User.email==student_email).one()
            except exc.NoResultFound:
                self.request.session.flash('Emailadresse nicht gefunden!', queue='errors')
                return {'lecture': lecture,
                        'tutorials': tutorials
                        }
            tutorial = [t for t in tutorials if t.id == new_tutorial]
            if len(tutorial)!=1:
                raise HTTPForbidden('Tutorial gehoert nicht zu dieser Vorlesung!')
            tutorial = tutorial[0]
            if student in lecture.students.all():
                self.request.session.flash('Der Student ist in diese Vorlesung bereits eingetragen!', queue='errors')
            else:
                lrs = self.request.db.query(models.LectureRemovedStudent).get((lecture.id, student.id))
                if lrs:
                    self.request.db.delete(lrs)
                #ls = request.db.query(models.LectureStudent).get((lecture.id, request.user.id))
                #if ls:
                #       oldtutorial = ls.tutorial
                #else:
                ls = models.LectureStudent()
                ls.lecture = lecture
                ls.student = student
                oldtutorial = None
                ls.tutorial = tutorial
                if not ls in self.request.db: self.request.db.add(ls)
                self.request.db.commit()
                self.request.session.flash('Der Student %s wurde in das Tutorial %s (%s) eingetragen' % (student, tutorial.time.__html__(), tutorial.tutor_name), queue='messages')
        return {'lecture': lecture,
                'tutorials': tutorials
                }

def sendMailAfterSwitch(request, student1, student2, lecture):
    message = Message(subject='MÜSLI: Sie haben ihre Übungsgruppe getauscht',
            sender=('%s <%s>' % (request.config['contact']['name'], request.config['contact']['email'])),
            to=[student1.email],
            body='Hallo %s!\n\nSie haben erfolgreich das Tutorium mit Ihrem Kommilitonen %s in der Vorlesung %s getauscht.'
                 '\nWenn dies nicht nach Ihrem Wunsch geschehen ist, bitte wenden Sie sich an Ihren Tutor oder Dozenten.'
                 '\n\nMit freundlichen Grüßen,\n  Das MÜSLI-Team\n' % (student1.name, student2.name, lecture.name))
    muesli.mail.sendMail(message)

@view_config(route_name='lecture_switch_students', renderer='muesli.web:templates/lecture/switch_students.pt', context=LectureContext, permission='edit')
class SwitchStudents(object):
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
        request.javascript.append('jquery/jquery.min.js')
        request.javascript.append('jquery/select2.min.js')

    def __call__(self):
        lecture = self.db.query(models.Lecture).get(self.lecture_id)
        tutorials = lecture.tutorials
        students = lecture.students.all()
        if self.request.method == 'POST':
            student1_id = int(self.request.POST['student1'])
            student2_id = int(self.request.POST['student2'])
            student1 = self.db.query(models.User).filter(models.User.id==student1_id).one()
            student2 = self.db.query(models.User).filter(models.User.id == student2_id).one()

            ls1 = self.request.db.query(models.LectureStudent).get((lecture.id, student1.id))
            ls2 = self.request.db.query(models.LectureStudent).get((lecture.id, student2.id))

            if student1_id == student2_id:
                self.request.session.flash('Student kann nicht mit sich selbst getauscht werden!', queue='errors')
            elif ls1.tutorial==ls2.tutorial:
                self.request.session.flash('Die beiden Studenten sind im gleichen Tutorium!', queue='errors')
            else:
                tmp = ls1.tutorial
                ls1.tutorial = ls2.tutorial
                ls2.tutorial = tmp
                self.request.db.commit()
                sendMailAfterSwitch(self.request, student1, student2, lecture)
                sendMailAfterSwitch(self.request, student2, student1, lecture)
                muesli.web.viewsTutorial.sendChangesMailSubscribe(self.request, ls1.tutorial, student1, ls2.tutorial)
                muesli.web.viewsTutorial.sendChangesMailSubscribe(self.request, ls2.tutorial, student2, ls1.tutorial)
                muesli.web.viewsTutorial.sendChangesMailUnsubscribe(self.request, ls1.tutorial, student2, ls2.tutorial)
                muesli.web.viewsTutorial.sendChangesMailUnsubscribe(self.request, ls2.tutorial, student1, ls1.tutorial)
                self.request.session.flash('Sie haben die Tutorien von {} und {} vertauscht'.format(student1.name(),student2.name()), queue='messages')

        return {'lecture': lecture,
                'tutorials': tutorials,
                'students': students
                }


@view_config(route_name='lecture_edit', renderer='muesli.web:templates/lecture/edit.pt', context=LectureContext, permission='edit')
class Edit:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
    def __call__(self):
        lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count')).get(self.lecture_id)
        form = LectureEdit(self.request, lecture)
        assistants = self.db.query(models.User).filter(models.User.is_assistant==1).order_by(models.User.last_name).all()
        if self.request.method == 'POST' and form.processPostData(self.request.POST):
            form.saveValues()
            self.request.db.commit()
        names = self.request.config['lecture_types'][lecture.type]
        pref_subjects = lecture.pref_subjects()
        pref_count = sum([pref[0] for pref in pref_subjects])
        subjects = lecture.subjects()
        student_count = sum([subj[0] for subj in subjects])
        return {'lecture': lecture,
                'names': names,
                'pref_count': pref_count,
                'subjects': subjects,
                'student_count': student_count,
                'categories': utils.categories,
                'exams': dict([[cat['id'], lecture.exams.filter(models.Exam.category==cat['id'])] for cat in utils.categories]),
                'assistants': assistants,
                'form': form}

@view_config(route_name='lecture_delete', context=LectureContext, permission='delete_lecture')
def delete(request):
    lecture = request.context.lecture
    if lecture.tutorials:
        request.session.flash('Vorlesung hat noch Übungsgruppen!', queue='errors')
    elif lecture.tutors:
        request.session.flash('Vorlesung hat noch Tutoren!', queue='errors')
    elif lecture.lecture_students.all():
        request.session.flash('Vorlesung hat noch Studenten', queue='errors')
    elif lecture.lecture_removed_students.all():
        request.session.flash('Vorlesung hat noch gelöschte Studenten', queue='errors')
    elif lecture.exams.all():
        request.session.flash('Vorlesung hat noch Testate', queue='errors')
    elif lecture.gradings:
        request.session.flash('Vorlesung hat noch Benotungen', queue='errors')
    elif lecture.time_preferences.all():
        request.session.flash('Vorlesung hat noch Präferenzen', queue='errors')
    else:
        lecture.assistants = []
        request.db.delete(lecture)
        request.db.commit()
        request.session.flash('Vorlesung gelöscht', queue='messages')
    return HTTPFound(location=request.route_url('lecture_list'))

@view_config(route_name='lecture_change_assistants', context=LectureContext, permission='change_assistant')
def change_assistants(request):
    lecture = request.context.lecture
    if request.method == 'POST':
        for nr, assistant in enumerate(lecture.assistants):
            if 'change-%i' % assistant.id in request.POST:
                new_assistant = request.db.query(models.User).get(request.POST['assistant-%i' % assistant.id])
                if new_assistant in lecture.assistants:
                    request.session.flash('Assistent ist bereits in Vorlesung eingetragen', queue='errors')
                else:
                    lecture.assistants[nr] = new_assistant
            if 'remove-%i' % assistant.id in request.POST:
                del lecture.assistants[nr]
        if 'add-assistant' in request.POST:
            if request.POST['new-assistant'] == "None":
                request.session.flash('Bitte einen Assistenten auswählen', queue='errors')
            else:
                new_assistant = request.db.query(models.User).get(request.POST['new-assistant'])
                if new_assistant and new_assistant not in lecture.assistants:
                    lecture.assistants.append(new_assistant)
    if request.db.new or request.db.dirty or request.db.deleted:
        if len(lecture.assistants)>0:
            lecture.old_assistant = lecture.assistants[0]
        else:
            lecture.old_assistant = None
        request.db.commit()
    return HTTPFound(location=request.route_url('lecture_edit', lecture_id = lecture.id))

@view_config(route_name='lecture_preferences', renderer='muesli.web:templates/lecture/preferences.pt', context=LectureContext, permission='edit')
class Preferences:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
    def __call__(self):
        lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count')).get(self.lecture_id)
        names = self.request.config['lecture_types'][lecture.type]
        pref_subjects = lecture.pref_subjects()
        pref_count = sum([pref[0] for pref in pref_subjects])
        subjects = lecture.subjects()
        student_count = sum([subj[0] for subj in subjects])
        times = lecture.prepareTimePreferences(user=None)
        times = sorted([t for t in times], key=lambda s:s['time'].value)
        #print(times)
        return {'lecture': lecture,
                'names': names,
                'pref_subjects': pref_subjects,
                'pref_count': pref_count,
                'subjects': subjects,
                'times': times,
                'student_count': student_count,
                'categories': utils.categories,
                'exams': dict([[cat['id'], lecture.exams.filter(models.Exam.category==cat['id'])] for cat in utils.categories]),
                }

@view_config(route_name='lecture_prefhistogram', context=LectureContext, permission='edit')
class PrefHistogram(MatplotlibView):
    def __init__(self, request):
        MatplotlibView.__init__(self)
        self.request=request
        lecture = self.request.context.lecture
        time = self.request.matchdict['time']
        preferences = self.request.db.query(sa.func.count(TimePreference.penalty),TimePreference.penalty).filter(TimePreference.lecture_id==lecture.id)\
                .filter(TimePreference.time==time).group_by(TimePreference.penalty).order_by(TimePreference.penalty).all()
        prefdict = {}
        for count, penalty in preferences:
            prefdict[penalty]=count
        self.bars = [prefdict.get(p['penalty'],0) for p in utils.preferences]
        self.inds = list(range(len(utils.preferences)))
        self.xticks = [p['name'] for p in utils.preferences]
        self.label=types.TutorialTime(time).__html__()
    def __call__(self):
        ax = self.fig.add_subplot(111)
        if self.bars:
            ax.bar(self.inds, self.bars, color='red')
            ax.set_xticks([i+0.4 for i in self.inds])
            ax.set_xticklabels(self.xticks)
        ax.set_title(self.label)
        return self.createResponse()

@view_config(route_name='lecture_add', renderer='muesli.web:templates/lecture/add.pt', context=GeneralContext, permission='create_lecture')
class Add:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
    def __call__(self):
        form = LectureAdd(self.request)
        if self.request.method == 'POST' and form.processPostData(self.request.POST):
            lecture = models.Lecture()
            lecture.assistants.append(self.request.user)
            form.obj = lecture
            form.saveValues()
            self.request.db.add(lecture)
            self.request.db.commit()
            return HTTPFound(self.request.route_url('lecture_edit', lecture_id = lecture.id))
        return {'form': form}

@view_config(route_name='lecture_remove_tutor', context=LectureContext, permission='edit')
class RemoveTutor:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
        self.tutor_id = request.matchdict['tutor_id']
        self.tutorials = request.context.lecture.tutorials
    def __call__(self):
        lecture = self.db.query(models.Lecture).get(self.lecture_id)
        tutor = self.db.query(models.User).get(self.tutor_id)
        for tutorial in self.tutorials:
            if tutorial.tutor_id == int(self.tutor_id):
                tutorial.tutor = None
        if not tutor:
            return
        if not tutor in lecture.tutors:
            return
        lecture.tutors.remove(tutor)
        self.db.commit()
        return HTTPFound(location=self.request.route_url('lecture_edit', lecture_id=lecture.id))

@view_config(route_name='lecture_export_students_html', renderer='muesli.web:templates/lecture/export_students_html.pt', context=LectureContext, permission='edit')
class ExportStudentsHtml:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
    def __call__(self):
        lecture = self.db.query(models.Lecture).get(self.lecture_id)
        students = lecture.lecture_students_for_tutorials([])
        if 'subject' in self.request.GET:
            students = students.filter(models.LectureStudent.student.has(models.User.subject==self.request.GET['subject']))
        return {'lecture': lecture,
                'lecture_students': students}

@view_config(route_name='lecture_email_tutors', renderer='muesli.web:templates/lecture/email_tutors.pt', context=LectureContext, permission='mail_tutors')
def emailTutors(request):
    db = request.db
    lecture = request.context.lecture
    form = LectureEmailTutors(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        tutors = lecture.tutors
        message = Message(subject=form['subject'],
                sender=request.user.email,
                to= [assistant.email for assistant in lecture.assistants],
                bcc=[t.email for t in tutors],
                body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            sendMail(message,request)
        except:
            pass
        else:
            if request.permissionInfo.has_permission('edit'):
                routeback_url = 'lecture_edit'
            else:
                routeback_url = 'lecture_view'
            request.session.flash('A mail has been sent to all tutors of this lecture', queue='messages')
            return HTTPFound(location=request.route_url(routeback_url, lecture_id=lecture.id))
    return {'lecture': lecture,
            'form': form}

@view_config(route_name='lecture_email_students', renderer='muesli.web:templates/lecture/email_students.pt', context=LectureContext, permission='edit')
def emailStudents(request):
    db = request.db
    lecture = request.context.lecture
    form = LectureEmailStudents(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        students = lecture.students
        bcc = [s.email for s in students]
        if form['copytotutors']==0:
            bcc.extend([t.email for t in lecture.tutors])
        message = Message(subject=form['subject'],
                sender=request.user.email,
                to= [assistant.email for assistant in lecture.assistants],
                bcc=bcc,
                body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            sendMail(message,request)
        except:
            pass
        else:
            request.session.flash('A mail has been sent to all students of this lecture', queue='messages')
            return HTTPFound(location=request.route_url('lecture_edit', lecture_id=lecture.id))
    return {'lecture': lecture,
            'form': form}

@view_config(route_name='lecture_view_removed_students', renderer='muesli.web:templates/lecture/view_removed_students.pt', context=LectureContext, permission='edit')
def viewRemovedStudents(request):
    db = request.db
    lecture = request.context.lecture
    ls = lecture.lecture_removed_students
    ls = ls.join(LectureRemovedStudent.student).order_by(User.last_name, User.first_name)
    return {'lecture': lecture,
            'removed_students': ls}

@view_config(route_name='lecture_export_totals', renderer='muesli.web:templates/lecture/export_totals.pt', context=LectureContext, permission='edit')
def exportTotals(request):
    db = request.db
    lecture = request.context.lecture
    # TODO: Order by tutor/student
    ls = lecture.lecture_students_for_tutorials(order=False)
    Tutor = sqlalchemy.orm.aliased(models.User)
    ls = ls.join(models.LectureStudent.student).join(models.LectureStudent.tutorial).join(Tutor, models.Tutorial.tutor).order_by(Tutor.last_name, models.User.last_name, models.User.first_name)
    lecture_results = lecture.getLectureResults(students=ls)
    results = DictOfObjects(lambda: DictOfObjects(lambda: {}))
    for res in lecture_results:
        results[res.student_id]['results'][res.Exam.id] = res.points
    cat_results = lecture.getLectureResultsByCategory(students=ls)
    for res in cat_results:
        results[res.student_id]['totals'][res.category] = res.points
    gresults = lecture.getGradingResults(students = ls)
    grading_results = DictOfObjects(lambda: {})
    for res in gresults:
        grading_results[res.student_id][res.grading_id] = res.grade
    exams_by_category = [
            {'id':cat['id'], 'name': cat['name'], 'exams': lecture.exams.filter(models.Exam.category==cat['id']).all()} for cat in utils.categories]
    exams_by_category = [cat for cat in exams_by_category if cat['exams']]
    return {'lecture': lecture,
            'lecture_students': ls.all(),
            'categories': utils.categories,
            'results': results,
            'student_grades': grading_results,
            'exams_by_category': exams_by_category,
           }

@view_config(route_name='lecture_do_allocation', renderer='muesli.web:templates/lecture/do_allocation.pt', context=LectureContext, permission='edit')
def doAllocation(request):
    db = request.db
    lecture = request.context.lecture
    if not lecture.mode == 'prefs':
        return HTTPForbidden('This lecture is not in preferences mode')
    allocation = Allocation(lecture)
    result = allocation.doAllocation()
    prefs = {}
    for student in set(result['students_unhappy']+result['students_without_group']):
        p = [tp for tp in student.time_preferences if tp.lecture_id==lecture.id and tp.penalty < utils.students_unhappiness]
        prefs[student.id] = p
    lecture.mode = 'off'
    db.commit()
    return {'lecture': lecture,
                    'result': result,
                    'prefs': prefs}

@view_config(route_name='lecture_remove_allocation', context=LectureContext, permission='edit')
def removeAllocation(request):
    db = request.db
    lecture = request.context.lecture
    lecture.lecture_students.delete()
    lecture.mode = 'prefs'
    request.session.flash('Eintragung zurückgesetzt', queue='messages')
    db.commit()
    return HTTPFound(location=request.route_url('lecture_edit', lecture_id = lecture.id))


@view_config(route_name='lecture_set_preferences', context=LectureContext, permission='view')
def setPreferences(request):
    lecture = request.context.lecture
    times = lecture.prepareTimePreferences(user=request.user)
    row = 1
    tps = []
    while 'time-%i' % row in request.POST:
        time = types.TutorialTime(request.POST['time-%i' % row])
        tp = models.getOrCreate(models.TimePreference, request.db, (lecture.id, request.user.id, time))
        tp.penalty = int(request.POST['pref-%i' % row])
        tps.append(tp)
        row +=  1
    if lecture.minimum_preferences:
        valid = len([tp for tp in tps if tp.penalty < 100]) >= lecture.minimum_preferences
    else:
        #TODO: Works not for just one tutorial!
        min_number_of_times = len(tps)/100.0+1
        penalty_count = sum([1.0/tp.penalty for tp in tps])
        valid = penalty_count > min_number_of_times
    if not valid:
        request.db.rollback()
        request.session.flash('Fehler: Sie haben zu wenige Zeiten ausgewählt', queue='errors')
    else:
        request.db.commit()
        request.session.flash('Präferenzen gespeichert.', queue='messages')
    return HTTPFound(location=request.route_url('lecture_view', lecture_id = lecture.id))

@view_config(route_name='lecture_remove_preferences', context=LectureContext, permission='view')
def removePreferences(request):
    lecture = request.context.lecture
    lecture.time_preferences.filter(models.TimePreference.student_id == request.user.id).delete()
    request.db.commit()
    request.session.flash('Präferenzen wurden entfernt.', queue='messages')
    return HTTPFound(location=request.route_url('lecture_view', lecture_id = lecture.id))

@view_config(route_name='lecture_view_points', renderer='muesli.web:templates/lecture/view_points.pt', context=LectureContext, permission='view_own_points')
def viewPoints(request):
    lecture = request.context.lecture
    try:
        ls = lecture.lecture_students.filter(models.LectureStudent.student_id == request.user.id).one()
    except exc.NoResultFound:
        return HTTPForbidden()
    visible_exams = lecture.exams.filter((models.Exam.results_hidden==False)|(models.Exam.results_hidden==None))
    exams = visible_exams.all()
    exams_by_category = [
            {'id':cat['id'], 'name': cat['name'], 'exams': visible_exams.filter(models.Exam.category==cat['id']).all()} for cat in utils.categories]
    exams_by_category = [cat for cat in exams_by_category if cat['exams']]
    results = {}
    for exam in exams:
        results[exam.id] = exam.getResultsForStudent(ls.student)
    for exams in exams_by_category:
        sum_all = sum([x for x in [results[e.id]['sum'] for e in exams['exams']] if x])
        max_all = sum([x for x in [e.getMaxpoints() for e in exams['exams']] if x])
        exams['sum'] = sum_all
        exams['max'] = max_all
    exams_with_registration = [e for e in lecture.exams.all() if e.registration != None]
    registrations = {}
    for reg in request.db.query(models.ExamAdmission).filter(models.ExamAdmission.exam_id.in_([e.id for e in exams_with_registration])).filter(models.ExamAdmission.student_id == ls.student_id).all():
        registrations[reg.exam_id] = reg
    for exam in exams_with_registration:
        if not exam.id in registrations:
            registrations[exam.id] = models.ExamAdmission(exam=exam, student=request.user)
        if 'registration-%s' % exam.id in request.POST:
            newreg = request.POST['registration-%s' % exam.id]
            if newreg == '':
                newreg = None
            elif newreg == '0':
                newreg = False
            elif newreg == '1':
                newreg = True
            else:
                raise ValueError
            registrations[exam.id].registration=newreg
            request.db.merge(registrations[exam.id])
            request.db.commit()
    exams_with_admission = [e for e in lecture.exams.all() if e.admission != None]
    admissions = {}
    for adm in request.db.query(models.ExamAdmission).filter(models.ExamAdmission.exam_id.in_([e.id for e in exams_with_admission])).filter(models.ExamAdmission.student_id == ls.student_id).all():
        admissions[adm.exam_id] = adm
    for exam in exams_with_admission:
        if not exam.id in admissions:
            admissions[exam.id] = models.ExamAdmission(exam=exam, student=request.user)
    grades = request.user.student_grades.filter(models.StudentGrade.grading.has(models.Grading.lecture_id == lecture.id)).all()
    return {
            'lecture': lecture,
            'results': results,
            'exams_by_category': exams_by_category,
            'registrations': registrations,
            'admissions': admissions,
            'grades': grades,
            }
    return HTTPFound(location=request.route_url('lecture_view', lecture_id = lecture.id))

@view_config(route_name='lecture_export_yaml', context=GeneralContext, permission='export_yaml')
def exportYaml(request):
    lectures = request.db.query(models.Lecture)
    if not "show_all" in request.GET:
        lectures = lectures.filter(models.Lecture.is_visible==True)
    out = []
    for lecture in lectures.all():
        lecture_dict = {}
        tutors = set([tutorial.tutor for tutorial in lecture.tutorials])
        lecture_dict['tutors'] = [tutor.name() for tutor in tutors if tutor!= None]
        lecture_dict['name'] = lecture.name
        lecture_dict['lecturer'] = lecture.lecturer
        lecture_dict['student_count'] = lecture.lecture_students.count()
        lecture_dict['term'] = lecture.term.__html__()
        out.append(lecture_dict)
    response = Response(content_type='application/x-yaml')
    response.text = yaml.safe_dump(out, allow_unicode=True, default_flow_style=False)
    return response

@view_config(route_name='lecture_export_yaml_details',context = GeneralContext, permission = 'export_yaml')
def exportYaml_details(request):
    lectures = request.db.query(models.Lecture)
    if not "show_all" in request.GET:
        lectures = lectures.filter(models.Lecture.is_visible == True)
    out = []
    for lecture in lectures.all():
        lecture_dict = {}
        lecture_dict['tutorials'] = []
        for tutorial in lecture.tutorials:
            vtutor = 'tutor: ' + tutorial.tutor.name() if tutorial.tutor!=None else 'tutor: '
            vemail = 'email: ' + tutorial.tutor.email  if tutorial.tutor!=None else 'email: '
            vplace = 'place: ' + tutorial.place
            vtime = 'time: '+ tutorial.time.__html__()
            vcomment = 'comment: ' + tutorial.comment
            tutorialItem = (vtutor.replace("'",""),vemail, vplace.replace("'",""), vtime.replace("'",""),vcomment.replace("'",""))
            lecture_dict['tutorials'].append(tutorialItem)
        lecture_dict['name'] = lecture.name
        lecture_dict['lecturer'] = lecture.lecturer
        lecture_dict['student_count'] = lecture.lecture_students.count()
        lecture_dict['term'] = lecture.term.__html__()
        out.append(lecture_dict)
        response = Response(content_type='application/x-yaml')
    response.body = yaml.safe_dump(out, allow_unicode=True, default_flow_style=False)
    return response


class ExcelExport:
    def __init__(self, request):
        self.request = request
        self.w = Workbook()

    def createResponse(self):
        response = Response(content_type='application/vnd.ms-excel')
        response.body = save_virtual_workbook(self.w)
        return response


@view_config(route_name='lecture_export_excel', context=GeneralContext, permission='view')
class DoExport(ExcelExport):
    def __call__(self):
        lectures = self.request.db.query(models.Lecture)
        lectures = lectures.filter(models.Lecture.is_visible)
        w = self.w

        # sheet Tutorials
        worksheet_tutorials = w.active
        worksheet_tutorials.title = 'Tutorials'
        header = ['Tutor FirstName',
                  'Tutor LastName',
                  'Tutor Email',
                  'Tutorial Information',
                  'Student Count',
                  'Tutorial Room',
                  'Time',
                  'Comments']
        worksheet_tutorials.append(header)
        worksheet_tutorials.row_dimensions[1].font = Font(bold=True)
        row_index = 2
        for lecture in lectures.all():
            tutorial_list = []
            lecture_name = lecture.name
            for tutorial in lecture.tutorials:
                vtutor = tutorial.tutor.name() if tutorial.tutor is not None else 'None'
                vtutor_first_name = tutorial.tutor.first_name if tutorial.tutor is not None else 'None'
                vtutor_last_name = tutorial.tutor.last_name if tutorial.tutor is not None else 'None'
                vemail = tutorial.tutor.email if tutorial.tutor is not None else 'None'
                vplace = tutorial.place
                vtime = tutorial.time.__html__()
                vcomment = tutorial.comment
                vstudent = len(tutorial.students.all())
                tutorial_item = (vtutor_first_name, vtutor_last_name, vemail,
                                 lecture_name, vstudent, vplace, vtime, vcomment)
                tutorial_list.append(tutorial_item)
            # add summary lecture
            new_list = []
            lecture_item = ('', lecture.lecturer, '', lecture_name,
                            lecture.lecture_students.count(), '', lecture.term.__html__(), '')
            new_list.append(lecture_item)
            # sort by tutor fistName
            tutorial_list = sorted(tutorial_list)
            tutorial_index = 1
            for item in tutorial_list:
                new_item = (item[0], item[1], item[2], item[3]+' Uebungsgruppe: '+str(tutorial_index),
                            item[4], item[5], item[6], item[7])
                new_list.append(new_item)
                tutorial_index = tutorial_index + 1
            # add to sheet
            for item in new_list:
                for col, d in enumerate(item, 1):
                    worksheet_tutorials.cell(row=row_index, column=col, value=d)
                row_index = row_index + 1
        # set column width
        for column_cells in worksheet_tutorials.columns:
            max_length = max(len(str(cell.value)) for cell in column_cells)
            worksheet_tutorials.column_dimensions[column_cells[0].column].width = max_length*1.2
        return self.createResponse()
