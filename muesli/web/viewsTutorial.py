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
from muesli.mail import Message
import muesli.mail
from muesli.web.forms import *
from muesli.web.context import *

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden, HTTPFound
from pyramid.url import route_url
from sqlalchemy.orm import exc
import sqlalchemy

import re
import os

import PIL.Image
import PIL.ImageDraw
import io

@view_config(route_name='tutorial_view', renderer='muesli.web:templates/tutorial/view.pt', context=TutorialContext, permission='viewOverview')
class View:
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.tutorial_ids = request.matchdict['tutorial_ids']
    def __call__(self):
        tutorials = self.request.context.tutorials
        lecture_students = self.request.context.lecture.lecture_students_for_tutorials(tutorials).options(sqlalchemy.orm.joinedload(LectureStudent.student))
        students = [ls.student for ls in lecture_students] #self.db.query(models.User).filter(filterClause)
        tutorial = tutorials[0]
        other_tutorials = tutorial.lecture.tutorials
        return {'tutorial': tutorial,
                'tutorials': tutorials,
                'tutorial_ids': self.tutorial_ids,
                'other_tutorials': other_tutorials,
                'students': students,
                'categories': utils.categories,
                'exams': dict([[cat['id'], tutorial.lecture.exams.filter(models.Exam.category==cat['id'])] for cat in utils.categories]),
                'names': self.request.config['lecture_types'][tutorial.lecture.type],
                'old_tutorial_id': None  #see move_student
                }

@view_config(route_name='tutorial_occupancy_bar')
class OccupancyBar:
    def __init__(self, request):
        self.request = request
        self.count = int(request.matchdict['count'])
        self.max_count = int(request.matchdict['max_count'])
        self.width = 60
        self.height = 10
        self.color1 = (0,0,255)
        self.color2 = (140,140,255)
    def __call__(self):
        image = PIL.Image.new('RGB', (self.width,self.height),(255,255,255))
        draw = PIL.ImageDraw.Draw(image)
        # prevent 0-division error
        if self.max_count > 0:
            draw.rectangle([(0,0),(float(self.width)*self.max_count/self.max_count,10)], fill=self.color2)
            draw.rectangle([(0,0),(float(self.width)*self.count/self.max_count,10)], fill=self.color1)
        else:
            draw.rectangle([(0,0),(float(self.width),10)], fill=self.color1)
        output = io.BytesIO()
        image.save(output, format='PNG')
        response = Response()
        response.content_type = 'image/png'
        response.cache_control = 'max-age=86400'
        response.body = output.getvalue()
        output.close()
        return response

@view_config(route_name='tutorial_add', renderer='muesli.web:templates/tutorial/add.pt', context=LectureContext, permission='edit')
class Add:
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
            form.message = "Neue Übungsgruppe angelegt."
        return {'lecture': lecture,
                'names': self.request.config['lecture_types'][lecture.type],
                'form': form,
                'error_msg': error_msg}

@view_config(route_name='tutorial_duplicate', renderer='muesli.web:templates/tutorial/add.pt', context=LectureContext, permission='edit')
class Duplicate(object):
    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.lecture_id = request.matchdict['lecture_id']
        self.tutorial_id = request.matchdict['tutorial_id']
    def __call__(self):
        error_msg = ''
        orig_tutorial = self.db.query(models.Tutorial).get(self.tutorial_id)
        lecture = self.db.query(models.Lecture).get(self.lecture_id)

        form = TutorialEdit(self.request, orig_tutorial)
        if self.request.method == 'POST' and form.processPostData(self.request.POST):
            tutorial = models.Tutorial()
            tutorial.lecture = orig_tutorial.lecture
            tutorial.place=orig_tutorial.place
            tutorial.time = orig_tutorial.time
            tutorial.max_students=orig_tutorial.max_students
            tutorial.comment=orig_tutorial.comment
            tutorial.is_special=orig_tutorial.is_special
            form.obj = tutorial
            form.saveValues()
            self.request.db.commit()
            form.message = "Neue Übungsgruppe angelegt."
        return {'lecture': lecture,
                'names': self.request.config['lecture_types'][lecture.type],
                'form': form,
                'error_msg': error_msg}

@view_config(route_name='tutorial_delete', context=TutorialContext, permission='edit')
def delete(request):
    for tutorial in request.context.tutorials:
        if tutorial.student_count:
            request.session.flash('Übungsgruppe ist nicht leer!', queue='errors')
        else:
            for lrs in tutorial.lecture_removed_students:
                lrs.tutorial = None
            request.db.delete(tutorial)
            request.session.flash('Übungsgruppe gelöscht.', queue='messages')
    request.db.commit()
    return HTTPFound(location=request.route_url('lecture_edit', lecture_id = request.context.lecture.id))

@view_config(route_name='tutorial_edit', renderer='muesli.web:templates/tutorial/edit.pt', context=TutorialContext, permission='edit')
class Edit:
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
            form.message = "Änderungen gespeichert"
        return {'tutorial': tutorial,
                'names': self.request.config['lecture_types'][tutorial.lecture.type],
                'form': form,
                'error_msg': error_msg}

@view_config(route_name='tutorial_results', renderer='muesli.web:templates/tutorial/results.pt', context=TutorialContext, permission='viewAll')
def results(request):
    tutorials = request.context.tutorials
    lecture = request.context.lecture
    lecture_students = lecture.lecture_students_for_tutorials(tutorials=tutorials).options(sqlalchemy.orm.joinedload(LectureStudent.student))\
            .options(sqlalchemy.orm.joinedload(LectureStudent.tutorial)).all()
    lecture_results = lecture.getLectureResults(students=lecture_students)
    results = lecture.getPreparedLectureResults(lecture_results)
    cat_maxpoints = dict([cat['id'], 0] for cat in utils.categories)
    for exam in lecture.exams:
        cat_maxpoints[exam.category] += exam.getMaxpoints()
    request.javascript.append('jquery/jquery.min.js')
    request.javascript.append('jquery/jquery.tablesorter.min.js')
    return {'tutorials': tutorials,
            'tutorial_ids': request.context.tutorial_ids_str,
            'lecture_students': lecture_students,
            'results': results,
            'names': request.config['lecture_types'][lecture.type],
            'categories': utils.categories,
            'cat_maxpoints': cat_maxpoints,
            'exams_by_cat': dict([[cat['id'], lecture.exams.filter(models.Exam.category==cat['id']).all()] for cat in utils.categories]),
            }

@view_config(route_name='tutorial_take', context=TutorialContext, permission='take_tutorial')
def take(request):
    tutorials = request.context.tutorials
    for tutorial in tutorials:
        if tutorial.tutor_id:
            request.session.flash('Für das Tutorial ist bereits ein Tutor eingetragen!', queue='errors')
        else:
            tutorial.tutor = request.user
            request.session.flash('Sie wurden als Übungsleiter eingetragen!', queue='messages')
    if request.db.dirty:
        request.db.commit()
    return HTTPFound(location=request.route_url('lecture_view', lecture_id = request.context.lecture.id))

@view_config(route_name='tutorial_resign_as_tutor', context=TutorialContext, permission='viewAll')
def resignAsTutor(request):
    tutorials = request.context.tutorials
    for tutorial in tutorials:
        if tutorial.tutor != request.user:
            request.session.flash('Sie sind nicht Tutor eines Tutorials', queue='errors')
        else:
            tutorial.tutor = None
            request.session.flash('Sie sind als Tutor zurückgetreten', queue='messages')
    if request.db.dirty or request.db.new or request.db.deleted:
        request.db.commit()
    return HTTPFound(location=request.route_url('lecture_view', lecture_id = request.context.lecture.id))

@view_config(route_name='tutorial_subscribe', context=TutorialContext, permission='subscribe')
def subscribe(request):
    tutorials = request.context.tutorials
    tutorial = tutorials[0]
    lecture = tutorial.lecture
    if tutorial.max_students > tutorial.students.count():
        lrs = request.db.query(models.LectureRemovedStudent).get((lecture.id, request.user.id))
        if lrs: request.db.delete(lrs)
        ls = request.db.query(models.LectureStudent).get((lecture.id, request.user.id))
        if ls:
            oldtutorial = ls.tutorial
        else:
            ls = models.LectureStudent()
            ls.lecture = lecture
            ls.student = request.user
            oldtutorial = None
        ls.tutorial = tutorial
        if not ls in request.db: request.db.add(ls)
        request.db.commit()
        if oldtutorial:
            sendChangesMailUnsubscribe(request, oldtutorial, request.user, toTutorial=tutorial)
        sendChangesMailSubscribe(request, tutorial, request.user, fromTutorial=oldtutorial)
        request.session.flash('Erfolgreich in Übungsgruppe eingetragen', queue='messages')
    else:
        request.session.flash('Maximale Teilnehmerzahl bereits erreicht', queue='errors')
        pass
    return HTTPFound(location=request.route_url('lecture_view', lecture_id=lecture.id))

@view_config(route_name='tutorial_unsubscribe', context=TutorialContext, permission='unsubscribe')
def unsubscribe(request):
    tutorials = request.context.tutorials
    tutorial = tutorials[0]
    lecture = tutorial.lecture
    ls = request.db.query(models.LectureStudent).get((lecture.id, request.user.id))
    if not ls or ls.tutorial_id != tutorial.id:
        return HTTPForbidden('Sie sind zu dieser Übungsgruppe nicht angemeldet')
    lrs = request.db.query(models.LectureRemovedStudent).get((lecture.id, request.user.id))
    if not lrs:
        lrs = models.LectureRemovedStudent()
        lrs.lecture = lecture
        lrs.student = request.user
    lrs.tutorial = tutorial
    if not lrs in request.db: request.db.add(lrs)
    request.db.delete(ls)
    request.db.commit()
    sendChangesMailUnsubscribe(request, tutorial, request.user)
    request.session.flash('Erfolgreich aus Übungsgruppe ausgetragen', queue='messages')
    return HTTPFound(location=request.route_url('start'))

@view_config(route_name='tutorial_remove_student', context=TutorialContext, permission='remove_student')
def removeStudent(request):
    student_id = int(request.matchdict['student_id'])
    ls = request.db.query(models.LectureStudent).get((request.context.lecture.id, student_id))
    if not ls:
        request.session.flash('Student in Vorlesung nicht gefunden!', queue='errors')
    else:
        lrs = models.LectureRemovedStudent()
        lrs.student_id = student_id
        lrs.lecture_id = ls.lecture_id
        lrs.tutorial_id = ls.tutorial_id
        request.db.add(lrs)
        request.db.delete(ls)
        request.db.commit()
        request.session.flash('Student aus Übungsgruppe ausgetragen!', queue='messages')
    if request.referrer:
        return HTTPFound(location=request.referrer)
    else:
        return HTTPFound(location=request.route_url('start'))

def sendChangesMailSubscribe(request, tutorial, student, fromTutorial=None):
    mail_preference = request.db.query(models.EmailPreferences).get((tutorial.tutor_id, tutorial.lecture.id))
    if mail_preference is None:
        mail_preference = models.EmailPreferences(tutorial.tutor_id, tutorial.lecture.id, True)
    if not tutorial.tutor or mail_preference.receive_status_mails == False:
        return
    text = 'In Ihre Übungsgruppe zur Vorlesung %s am %s hat sich %s eingetragen'\
            % (tutorial.lecture.name, tutorial.time.__html__(), student.name())
    if fromTutorial:
        text += ' (Wechsel aus der Gruppe am %s von %s).' % (fromTutorial.time.__html__(), fromTutorial.tutor.name() if fromTutorial.tutor else 'NN')
    else:
        text += '.'
    sendChangesMail(request, tutorial.tutor, text)

def sendChangesMailUnsubscribe(request, tutorial, student, toTutorial=None):
    mail_preference = request.db.query(models.EmailPreferences).get((tutorial.tutor_id, tutorial.lecture.id))
    if mail_preference is None:
        mail_preference = models.EmailPreferences(tutorial.tutor_id, tutorial.lecture.id, True)
    if not tutorial.tutor or mail_preference.receive_status_mails == False:
        return
    text = 'Aus Ihrer Übungsgruppe zur Vorlesung %s am %s hat sich %s ausgetragen'\
                    % (tutorial.lecture.name, tutorial.time.__html__(), student.name())
    if toTutorial:
        text += ' (Wechsel in die Gruppe am %s von %s).' % (toTutorial.time.__html__(), toTutorial.tutor.name() if toTutorial.tutor else 'NN')
    else:
        text += '.'
    sendChangesMail(request, tutorial.tutor, text)

def sendChangesMail(request, tutor, text):
    message = Message(subject='MÜSLI: Änderungen in Ihrer Übungsgruppe',
            sender=('%s <%s>' % (request.config['contact']['name'], request.config['contact']['email'])),
            to = [tutor.email],
            body='Hallo!\n\n%s\n\nMit freundlichen Grüßen,\n  Das MÜSLI-Team\n' % text)
    muesli.mail.sendMail(message)

@view_config(route_name='tutorial_email_preference', renderer='muesli.web:templates/tutorial/email_preference.pt', context=TutorialContext, permission='viewAll')
def email_preference(request):
    db = request.db
    tutorials = request.context.tutorials
    lecture = tutorials[0].lecture
    form = TutorialEmailPreference(request)
    mail_preference = db.query(models.EmailPreferences).get((request.user.id, lecture.id))
    if mail_preference is None:
        mail_preference = models.EmailPreferences(request.user.id, lecture.id, True)
    form['receive_status_mails'] = mail_preference.receive_status_mails
    if request.method == 'POST' and form.processPostData(request.POST):
        if form['receive_status_mails'] == 1:
            mail_preference.receive_status_mails = True
        else:
            mail_preference.receive_status_mails = False
        if not mail_preference in request.db:
            db.add(mail_preference)
        request.db.commit()
        request.session.flash('Your preferences have been updated', queue='messages')
    return {'tutorials': tutorials,
            'tutorial_ids': request.context.tutorial_ids_str,
            'lecture': lecture,
            'form': form}


@view_config(route_name='tutorial_email', renderer='muesli.web:templates/tutorial/email.pt', context=TutorialContext, permission='sendMail')
def email(request):
    db = request.db
    tutorials = request.context.tutorials
    lecture = tutorials[0].lecture
    form = TutorialEmail(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        lecture_students = lecture.lecture_students_for_tutorials(tutorials=tutorials)
        message = muesli.mail.Message(subject=form['subject'],
                sender=request.user.email,
                to=[request.user.email] if form['copytome']==0 else [],
                bcc=[ls.student.email for ls in lecture_students],
                body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            muesli.mail.sendMail(message,request)
        except:
            pass
        else:
            request.session.flash('A mail has been sent to all students of these tutorials', queue='messages')
            return HTTPFound(location=request.route_url('tutorial_view', tutorial_ids=request.context.tutorial_ids_str))
    return {'tutorials': tutorials,
            'tutorial_ids': request.context.tutorial_ids_str,
            'lecture': lecture,
            'form': form}

@view_config(route_name='tutorial_ajax_get_tutorial', renderer='json', context=LectureContext, permission='get_tutorials')
def ajaxGetTutorial(request):
    lecture = request.context.lecture
    student_id = request.POST['student_id']
    ls = request.db.query(models.LectureStudent).get((lecture.id, student_id))
    ret = {}
    if ls and ls.tutorial:
        ret = {'msg': 'sucessful'}
        ret['tutor'] = ls.tutorial.tutor.name() if ls.tutorial.tutor else 'N.N.'
        ret['time'] = ls.tutorial.time.formatted()
        return ret
    else:
        return {'msg': 'No Tutorial found!'}

@view_config(route_name='tutorial_assign_student', renderer='muesli.web:templates/tutorial/assign_student.pt', context=AssignStudentContext, permission='move')
def assign_student(request):
    student = request.context.student
    new_tutorial = request.context.tutorial
    lecture = new_tutorial.lecture
    lrs = request.db.query(models.LectureRemovedStudent).get((lecture.id, student.id))
    if lrs: request.db.delete(lrs)
    ls = request.db.query(models.LectureStudent).get((lecture.id, student.id))
    if ls:
        pass
    #       oldtutorial = ls.tutorial
    else:
        ls = models.LectureStudent()
        ls.lecture = lecture
        ls.student = student
    #       oldtutorial = None
    ls.tutorial = new_tutorial
    if not ls in request.db: request.db.add(ls)
    request.db.commit()
    #if oldtutorial:
    #       sendChangesMailUnsubscribe(request, oldtutorial, request.user, toTutorial=tutorial)
    #sendChangesMailSubscribe(request, tutorial, request.user, fromTutorial=oldtutorial)
    return {'student': student,
            'new_tutorial': new_tutorial}
