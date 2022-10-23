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
import datetime
import os
import traceback

import pyramid.exceptions
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response as render
from pyramid.response import FileResponse
from pyramid.view import view_config
from sqlalchemy.orm import joinedload

from muesli import DATAPROTECTION_HTML, CHANGELOG_HTML
from muesli.mail import Message, sendMail
from muesli.web.context import *
from muesli.web.forms import *
from muesli.web.tooltips import overview_tooltips


@view_config(route_name='overview', renderer='muesli.web:templates/overview.pt')
def overview(request):
    if not request.user:
        return HTTPFound(location=request.route_url('index'))
    tutorials_as_tutor = request.user.tutorials_as_tutor.options(joinedload(Tutorial.tutor),
                                                                 joinedload(Tutorial.lecture))
    tutorials = request.user.tutorials.options(joinedload(Tutorial.tutor), joinedload(Tutorial.lecture))
    lectures_as_assistant = request.user.lectures_as_assistant
    has_updated = request.db.query(models.UserHasUpdated).get(request.user.id)
    if has_updated is None:
        has_updated = models.UserHasUpdated(request.user.id, '0')
    uhu = has_updated.has_updated_info
    limit = muesli.utils.get_semester_limit()
    if uhu == limit:
        uboo = False
    else:
        uboo = True
    if has_updated not in request.db:
        request.db.add(has_updated)
    request.db.commit()
    if request.GET.get('show_all', '0') == '0':
        semesterlimit = utils.get_semester_limit()
        tutorials_as_tutor = tutorials_as_tutor.filter(Lecture.term >= semesterlimit)
        tutorials = tutorials.filter(Lecture.term >= semesterlimit)
        lectures_as_assistant = lectures_as_assistant.filter(Lecture.term >= semesterlimit)
    request.javascript.append('unsubscribe_modal_helpers.js')
    return {'uboo': uboo,
            'time_preferences': request.user.prepare_time_preferences(),
            'penalty_names': utils.penalty_names,
            'tutorials_as_tutor': tutorials_as_tutor.all(),
            'tutorials': tutorials.all(),
            'lectures_as_assistant': lectures_as_assistant.all(),
            'tooltips': overview_tooltips}


@view_config(route_name='start')
def start(request):
    return HTTPFound(location=request.route_url('overview'))


@view_config(route_name='admin', renderer='muesli.web:templates/admin.pt', context=GeneralContext, permission='admin')
def admin(_request):
    return {}


@view_config(
    route_name='test_exceptions',
    renderer='muesli.web:templates/test_exceptions.pt',
    context=GeneralContext,
    permission='admin'
)
def test_exceptions(request):
    if request.method == 'POST':
        if request.POST.get("HTTPInternalServerError"):
            raise Exception("Das ist eine Testnachricht!")
        if request.POST.get("HTTPBadRequest"):
            raise HTTPBadRequest("Dies ist eine Testfehlermeldung!")
        if request.POST.get("HTTPForbidden"):
            raise HTTPForbidden("Du kommsch hier ned rein!")
    return {}


@view_config(route_name='contact', renderer='muesli.web:templates/contact.pt')
def contact(_request):
    return {}


@view_config(route_name='index')
def index(request):
    if request.user:
        return HTTPFound(location=request.route_url('overview'))
    else:
        return HTTPFound(location=request.route_url('user_login'))


@view_config(route_name='email_all_users', renderer='muesli.web:templates/email_all_users.pt', context=GeneralContext,
             permission='admin')
def email_all_users(request):
    ttype = request.params.get('type', 'inform_message')
    form = EmailWrongSubject(ttype, request)
    semesterlimit = utils.get_semester_limit()
    students = request.db.query(models.User).filter(
        models.User.lecture_students.any(models.LectureStudent.lecture.has(models.Lecture.term >= semesterlimit))).all()
    headers = ['MUESLI-Information']
    table = []
    for s in students:
        table.append(s)
    if request.method == 'POST' and form.processPostData(request.POST):
        message = Message(subject=form['subject'],
                          sender=('%s <%s>' % (request.config['contact']['name'], request.config['contact']['email'])),
                          to=[],
                          bcc=[s.email for s in students],
                          body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            sendMail(message, request)
        except:
            pass
        else:
            request.session.flash('A Mail has been send to all students', queue='messages')
    return {'form': form,
            'type': ttype,
            'table': table,
            'headers': headers,
            'students': students}


@view_config(route_name='email_users', renderer='muesli.web:templates/email_users.pt', context=GeneralContext,
             permission='admin')
def email_users(request):
    ttype = request.params.get('type', 'unconfirmed')
    form = EmailWrongSubject(ttype, request)
    semesterlimit = utils.get_semester_limit()
    students = request.db.query(models.User).filter(
        models.User.lecture_students.any(models.LectureStudent.lecture.has(models.Lecture.term >= semesterlimit))).all()
    bad_students = []
    headers = []
    table = []
    if ttype == 'unconfirmed':
        headers = ['Anmeldedatum']
        bad_students = request.db.query(models.User).filter(models.User.password == None).all()
        for student in bad_students:
            table.append((student, student.confirmations[0].created_on))
    if request.method == 'POST' and form.processPostData(request.POST):
        message = Message(subject=form['subject'],
                          sender=('%s <%s>' % (request.config['contact']['name'], request.config['contact']['email'])),
                          to=[],
                          bcc=[s.email for s in bad_students],
                          body=form['body'])
        if request.POST['attachments'] not in ['', None]:
            message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
        try:
            sendMail(message, request)
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
def changelog(_request):
    return {'CHANGELOG_HTML': CHANGELOG_HTML}


@view_config(context=pyramid.exceptions.HTTPForbidden)
def forbidden(_exc, request):
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
def bad_request(e, request):
    if muesli.DEVELOPMENT_MODE:
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
def internal_server_error(e, request):
    if muesli.DEVELOPMENT_MODE:
        print("TRYING TO RECONSTRUCT EXCEPTION")
        traceback.print_exc()
        print("RAISING ANYHOW")
        raise e
    now = datetime.datetime.now().strftime("%d. %B %Y, %H:%M Uhr")
    traceback.print_exc()
    email = request.user.email if hasattr(request, 'user') and request.user else '<nobody>'
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
def datenschutzerklaerung_view(_request):
    return {'DATAPROTECTION_HTML': DATAPROTECTION_HTML}


@view_config(route_name='subject_admin', renderer='muesli.web:templates/subject_admin.pt', context=GeneralContext,
             permission='admin')
def subject_admin(request):
    query = select(models.Subject, func.count(models.User.id)).join(models.Subject.students).group_by(models.Subject.id)
    subjects_and_studentcounts = request.db.scalars(query).all()
    request.css.append('select2.min.css')
    request.javascript.append('select2_bullet_deletion_hack.js')
    request.javascript.append('select2.min.js')
    request.javascript.append('toast.min.js')
    request.css.append('toast.min.css')

    return {'subjects': subjects_and_studentcounts}
