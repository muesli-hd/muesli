# -*- coding: utf-8 -*-
#
# muesli/web/views.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2011, Ansgar Burchardt <ansgar (at) 43-1.org>
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

from muesli import models, utils, DATAPROTECTION_HTML, CHANGELOG_HTML
from muesli.web.forms import *
from muesli.web.context import *
from muesli.mail import Message, sendMail
from muesli.web.tooltips import start_tooltips

from pyramid import security
from pyramid.view import view_config
from pyramid.response import Response, FileResponse
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPInternalServerError, HTTPFound
from pyramid.renderers import render_to_response as render
import pyramid.exceptions
from pyramid.url import route_url
from sqlalchemy.orm import exc, joinedload
from hashlib import sha1
from markdown import markdown

import re
import os
import datetime
import traceback


@view_config(route_name='start', renderer='muesli.web:templates/start.pt')
def start(request):
    if not request.user:
        return HTTPFound(location = request.route_url('user_login'))
    tutorials_as_tutor = request.user.tutorials_as_tutor.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture))
    tutorials = request.user.tutorials.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture))
    lectures_as_assistant = request.user.lectures_as_assistant
    has_updated = request.db.query(models.UserHasUpdated).get(request.user.id)
    if has_updated is None:
        has_updated = models.UserHasUpdated(request.user.id, '0')
    uhu = has_updated.has_updated_info
    limit = muesli.utils.getSemesterLimit()
    if uhu == limit:
        uboo = False
    else:
        uboo = True
    if not has_updated in request.db:
        request.db.add(has_updated)
    request.db.commit()
    if request.GET.get('show_all', '0')=='0':
        semesterlimit = utils.getSemesterLimit()
        tutorials_as_tutor = tutorials_as_tutor.filter(Lecture.term >= semesterlimit)
        tutorials = tutorials.filter(Lecture.term >= semesterlimit)
        lectures_as_assistant = lectures_as_assistant.filter(Lecture.term >= semesterlimit)
    return {'uboo': uboo,
            'time_preferences': request.user.prepareTimePreferences(),
            'penalty_names': utils.penalty_names,
            'tutorials_as_tutor': tutorials_as_tutor.all(),
            'tutorials': tutorials.all(),
            'lectures_as_assistant': lectures_as_assistant.all(),
            'tooltips': start_tooltips}

@view_config(route_name='admin', renderer='muesli.web:templates/admin.pt', context=GeneralContext, permission='admin')
def admin(request):
    return {}

@view_config(route_name='contact', renderer='muesli.web:templates/contact.pt')
def contact(request):
    return {}

@view_config(route_name='index', renderer='muesli.web:templates/index.pt')
def index(request):
    return {}

@view_config(route_name='email_all_users', renderer='muesli.web:templates/email_all_users.pt', context=GeneralContext, permission='admin')
def emailAllUsers(request):
    ttype = request.params.get('type', 'inform_message')
    form = EmailWrongSubject(ttype, request)
    semesterlimit = utils.getSemesterLimit()
    students = request.db.query(models.User).filter(models.User.lecture_students.any(models.LectureStudent.lecture.has(models.Lecture.term >= semesterlimit))).all()
    headers = ['MUESLI-Information']
    table = []
    for s in students:
        table.append(s)
    if request.method == 'POST' and form.processPostData(request.POST):
        message = Message(subject=form['subject'],
                sender=('%s <%s>' % (request.config['contact']['name'], request.config['contact']['email'])),
                to= [],
                bcc=[s.email for s in students],
                body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            sendMail(message,request)
        except:
            pass
        else:
            request.session.flash('A Mail has been send to all students', queue='messages')
    return {'form': form,
            'type': ttype,
            'table': table,
            'headers': headers,
            'students': students}




@view_config(route_name='email_users', renderer='muesli.web:templates/email_users.pt', context=GeneralContext, permission='admin')
def emailUsers(request):
    ttype = request.params.get('type', 'wrong_subject')
    form = EmailWrongSubject(ttype, request)
    semesterlimit = utils.getSemesterLimit()
    students = request.db.query(models.User).filter(models.User.lecture_students.any(models.LectureStudent.lecture.has(models.Lecture.term >= semesterlimit))).all()
    bad_students = []
    headers = []
    table = []
    if ttype=='wrong_subject':
        headers = ['Fach', 'Beifach']
        for student in students:
            if not student.subject:
                continue
            lsub = student.subject.lower()
            if 'mathematik (la)' in lsub:
                if not ('hauptfach' in lsub or 'beifach' in lsub):
                    bad_students.append(student)
                elif not student.second_subject:
                    bad_students.append(student)
        for s in bad_students:
            table.append((s,s.subject, s.second_subject))
    elif ttype=='wrong_birthday':
        headers = ["Geburtstag"]
        validator = DateString()
        for student in students:
            try:
                date = validator.to_python(student.birth_date)
            except formencode.Invalid:
                bad_students.append(student)
        for s in bad_students:
            table.append((s,s.birth_date))
    elif ttype == 'unconfirmed':
        headers = ['Anmeldedatum']
        bad_students = request.db.query(models.User).filter(models.User.password == None).all()
        for student in bad_students:
            table.append((student, student.confirmations[0].created_on))
    if request.method == 'POST' and form.processPostData(request.POST):
        message = Message(subject=form['subject'],
                sender=('%s <%s>' % (request.config['contact']['name'], request.config['contact']['email'])),
                to= [],
                bcc=[s.email for s in bad_students],
                body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            sendMail(message,request)
        except:
            pass
        else:
            request.session.flash('A Mail has been send to all students with wrong subject', queue='messages')
    return {'form': form,
            'type': ttype,
            'table': table,
            'headers': headers,
            'students': bad_students}

@view_config(route_name='changelog', renderer='muesli.web:templates/changelog.pt')
def changelog(request):
    return {'CHANGELOG_HTML': CHANGELOG_HTML}


@view_config(context=pyramid.exceptions.HTTPForbidden)
def forbidden(exc, request):
    if "application/json" in request.headers.environ.get("HTTP_ACCEPT", ""):
        response = render(
            "json",
            {
                'error': "Sie haben nicht die noetigen Rechte um auf diese Seite zuzugreifen!",
                'route': request.path,
                'code': 403,
            },
        )
        response.status = 403
        response.content_type = "application/json"
        return response
    response = render('muesli.web:templates/HTTPForbidden.pt',
                      {},
                      request=request)
    response.status = 403
    return response

@view_config(context=pyramid.exceptions.HTTPBadRequest)
def badRequest(e, request):
    if not muesli.PRODUCTION_INSTANCE:
        print("TRYING TO RECONSTRUCT EXCEPTION")
        traceback.print_exc()
        print("RAISING ANYHOW")
        raise exc
    now = datetime.datetime.now().strftime("%d. %B %Y, %H:%M Uhr")
    traceback.print_exc()
    email = request.user.email if request.user else '<nobody>'
    if "application/json" in request.headers.environ.get("HTTP_ACCEPT", ""):
        response = render(
            "json",
            {
                'time': now, 'user': email,
                'contact': request.config['contact']['email'],
                'error': e.detail,
                'route': request.path,
                'code': e.code,
            },
        )
        response.content_type = "application/json"
        response.status = e.code
        return response
    response = render(
        'muesli.web:templates/HTTPBadRequest.pt',
        {'now': now, 'email': email, 'error': e.detail},
        request=request
    )
    response.status = e.code
    return response

@view_config(context=Exception)
def internalServerError(e, request):
    if not muesli.PRODUCTION_INSTANCE:
        print("TRYING TO RECONSTRUCT EXCEPTION")
        traceback.print_exc()
        print("RAISING ANYHOW")
        raise e
    now = datetime.datetime.now().strftime("%d. %B %Y, %H:%M Uhr")
    traceback.print_exc()
    email = request.user.email if request.user else '<nobody>'
    if "application/json" in request.headers.environ.get("HTTP_ACCEPT", ""):
        response = render(
            "json",
            {
                'time': now, 'user': email,
                'contact': request.config['contact']['email'],
                'error': "Bei der Beabeitung ist ein interner Fehler aufgetreten!",
                'route': request.path,
                'code': 500,
            },
        )
        response.content_type = "application/json"
        response.status = 500
        return response
    response = render('muesli.web:templates/HTTPInternalServerError.pt',
                      {'now': now, 'email': email},
                      request=request)
    response.status = 500
    return response


@view_config(name="favicon.ico")
def favicon_view(request):
    here = os.path.dirname(__file__)
    icon = os.path.join(here, "static", "favicon.ico")
    return FileResponse(icon, request=request)


@view_config(name='datenschutzerklaerung.html', renderer='muesli.web:templates/dataprotection.pt')
def datenschutzerklaerung_view(request):
    return {'DATAPROTECTION_HTML': DATAPROTECTION_HTML}
