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

from muesli import models
from muesli import utils
from muesli.web import forms
from muesli.web import context
from muesli.types import Term
import muesli

from pyramid import security
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound, HTTPForbidden
from pyramid.url import route_url
from sqlalchemy.orm import exc
from sqlalchemy import func, or_, not_
from hashlib import sha1
from muesli.mail import Message, sendMail

import re
import os
import datetime
import collections
import binascii


@view_config(route_name='user_login', renderer='muesli.web:templates/user/login.pt')
def login(request):
    form = forms.FormValidator(forms.UserLogin())
    if request.method == 'POST' and form.validate(request.POST):
        user = request.db.query(models.User).filter_by(email=form['email'].strip(), password=sha1(form['password'].encode('utf-8')).hexdigest()).first()
        if user is not None:
            security.remember(request, user.id)
            request.user = user
            url = request.route_url('start')
            return HTTPFound(location=url)
        request.session.flash('Nicht gefunden', queue='errors')
    return {'form': form, 'user': security.authenticated_userid(request)}


@view_config(route_name='debug_login', renderer='json', request_method='POST')
def debug_login(request):
    user = request.db.query(models.User).filter_by(email=request.POST['email'].strip(), password=sha1(request.POST['password'].encode('utf-8')).hexdigest()).first()
    if user:
        return {
            'result': 'ok',
            'token': request.create_jwt_token(user.id, admin=(user.is_admin))
        }
    else:
        return {
            'result': 'error'
        }

@view_config(route_name='debug_login', renderer='json', request_method='GET')
def refresh(request):
    user = request.db.query(models.User).get(request.authenticated_userid)
    if user:
        return {
            'result': 'ok',
            'token': request.create_jwt_token(user.id, admin=(user.is_admin))
        }
    else:
        return {
            'result': 'error'
        }



@view_config(route_name='user_logout')
def logout(request):
    security.forget(request)
    request.session.invalidate()
    return HTTPFound(location=request.route_url('index'))


@view_config(route_name='user_list', renderer='muesli.web:templates/user/list.pt', context=context.GeneralContext, permission='admin')
def listUser(request):
    users = request.db.query(models.User).order_by(models.User.last_name, models.User.first_name)
    if 'subject' in request.GET:
        users = users.filter(models.User.subject == request.GET['subject'])
    return {'users': users}


@view_config(route_name='user_list_subjects', renderer='muesli.web:templates/user/list_subjects.pt', context=context.GeneralContext, permission='admin')
def listSubjects(request):
    subjects = request.db.query(models.User.subject, func.count(models.User.id)).group_by(models.User.subject).order_by(models.User.subject)
    return {'subjects': subjects}


@view_config(route_name='user_list_subjects_by_term', renderer='muesli.web:templates/user/list_subjects_by_term.pt', context=context.GeneralContext, permission='admin')
def listSubjectsByTerm(request):
    settings = {
            'starting_term': '20121',          # SS 2012
            'minimal_count': 20,               # minimal count overall terms
            'exclude_lecture_name': 'Vorkurs'  # lecture name to exclude
    }
    subject_term_dict = collections.defaultdict(lambda: collections.defaultdict(int))
    terms = [str(x[0]) for x in request.db.query(models.Lecture.term)
            .filter(models.Lecture.term >= settings['starting_term'])
            .group_by(models.Lecture.term).order_by(models.Lecture.term.desc())]
    subjects_by_term = []
    table = request.db.query(models.Lecture.term, models.User.subject, func.count(models.User.id))\
            .join(models.LectureStudent)\
            .join(models.User)\
            .filter(models.Lecture.term >= settings['starting_term'])\
            .filter(not_(models.Lecture.name.contains(settings['exclude_lecture_name'])))\
            .group_by(models.User.subject, models.Lecture.term)\
            .order_by(models.Lecture.term, models.User.subject)
    for (term, subject, count) in table:
        subject = re.sub(r'\(.*\)', '', str(subject))
        subject = re.sub(r'\s$', '', str(subject))
        if subject == 'None' or subject == '':
            subject = '<ohne Studiengang>'
        subject_term_dict[subject][str(term)] += count
    for subject in sorted(subject_term_dict.keys()):
        counts = [((term), subject_term_dict[subject][term]) for term in terms]
        if sum([x[1] for x in counts]) > settings['minimal_count']:
            subjects_by_term.append((subject, counts))
    readable_terms = [Term(x) for x in terms]
    settings['starting_term'] = Term(settings['starting_term'])
    return {'subjects_by_term': subjects_by_term, 'terms': readable_terms, 'settings': settings}


@view_config(route_name='user_edit', renderer='muesli.web:templates/user/edit.pt', context=context.UserContext, permission='edit')
def edit(request):
    user_id = request.matchdict['user_id']
    user = request.db.query(models.User).get(user_id)
    lectures = user.lectures_as_assistant.all()
    form = forms.UserEdit(request, user)
    if request.method == 'POST' and form.processPostData(request.POST):
        if (form['is_assistant'] != user.is_assistant) and (form['is_assistant'] == 0):
            lectures = user.lectures_as_assistant.all()
            for l in lectures:
                for nr, ass in enumerate(l.assistants):
                    if ass.id == user.id:
                        del l.assistants[nr]
        form.saveValues()
        request.db.commit()
        request.session.flash('Daten geändert', queue='messages')
    return {'user': user,
            'form': form,
            'time_preferences': user.prepareTimePreferences(),
            'lectures_as_assistant': user.lectures_as_assistant.all(),
            'tutorials_as_tutor': user.tutorials_as_tutor.all(),
            'penalty_names': utils.penalty_names}


@view_config(route_name='user_delete', context=context.UserContext, permission='delete')
def delete(request):
    user = request.context.user
    if (user.tutorials.all()):
        request.session.flash('Benutzer %s ist zu Tutorien angemeldet und kann daher nicht gelöscht werden' % user, queue='errors')
        return HTTPFound(location=request.route_url('user_edit', user_id=user.id))
    elif user.tutorials_as_tutor.all():
        request.session.flash('Benutzer %s ist Tutor von Tutorien und kann daher nicht gelöscht werden' % user, queue='errors')
        return HTTPFound(location=request.route_url('user_edit', user_id=user.id))
    elif user.lectures_as_tutor:
        request.session.flash('Benutzer %s ist als Tutor eingetragen und kann daher nicht gelöscht werden' % user, queue='errors')
        return HTTPFound(location=request.route_url('user_edit', user_id=user.id))
    elif user.lectures_as_assistant.all():
        request.session.flash('Benutzer %s verwaltet Vorlesungen und kann daher nicht gelöscht werden' % user, queue='errors')
        return HTTPFound(location=request.route_url('user_edit', user_id=user.id))
    elif len(user.exercise_points) > 0:
        request.session.flash('Benutzer %s hat eingetragene Punkte und kann daher nicht gelöscht werden' % user, queue='errors')
        return HTTPFound(location=request.route_url('user_edit', user_id=user.id))
    elif len(user.student_grades.all()) > 0:
        request.session.flash('Benutzer %s hat eingetragene Noten und kann daher nicht gelöscht werden' % user, queue='errors')
        return HTTPFound(location=request.route_url('user_edit', user_id=user.id))
    elif len(user.tutorials_removed.all()) > 0:
        request.session.flash('Benutzer %s war in Tutorien angemeldet und kann daher nicht gelöscht werden' % user, queue='errors')
        return HTTPFound(location=request.route_url('user_edit', user_id=user.id))
    else:
        for c in user.confirmations:
            request.db.delete(c)
        # old_name = str(user)
        request.db.delete(user)
        request.db.commit()
        request.session.flash('Benutzer %s wurde gelöscht!' % user, queue='messages')
        return HTTPFound(location=request.route_url('admin'))


@view_config(route_name='user_delete_unconfirmed', renderer='muesli.web:templates/user/delete_unconfirmed.pt', context=context.GeneralContext, permission='admin')
def deleteUnconfirmed(request):
    potentially_bad_students = request.db.query(models.User).filter(models.User.password == None).all()
    bad_students = []
    # We delete everything older than 30 days
    limit = datetime.datetime.now() - datetime.timedelta(30)
    for student in potentially_bad_students:
        if student.confirmations[0].created_on < limit:
            bad_students.append((student, student.confirmations[0].created_on))
    bad_students.sort(key=lambda e: e[1])
    if request.method == 'POST' and 'delete' in request.POST:
        for student, date in bad_students:
            for c in student.confirmations:
                request.db.delete(c)
            request.db.delete(student)
        request.db.commit()
        request.session.flash('%i Studenten gelöscht' % len(bad_students), queue='messages')
        bad_students = []
    return {'unconfirmed_students': bad_students}

@view_config(route_name='user_doublets', renderer='muesli.web:templates/user/doublets.pt', context=context.GeneralContext, permission='admin')
def doublets(request):
    emails = [e.email for e in request.db.query(models.User.email)]
    doublets = collections.defaultdict(lambda: [])
    for user in request.db.query(models.User).all():
        doublets[user.email.lower()].append(user)
        # doublets[user.name().lower()].append(user)
    for key, value in list(doublets.items()):
        if len(value)<=1:
            del doublets[key]
    doublets_list = list(doublets.items())
    doublets_list.sort(key=lambda e: e[1][0].last_name)
    return {'doublets': doublets_list}


@view_config(route_name='user_update', renderer='muesli.web:templates/user/update.pt', context=context.GeneralContext, permission='update')
def update(request):
    form = forms.UserUpdate(request, request.user)
    if request.method == 'POST' and form.processPostData(request.POST):
        form.saveValues()
        request.db.commit()
        request.session.flash('Angaben geändert', queue='messages')
    return {'form': form}

@view_config(route_name='user_register', renderer='muesli.web:templates/user/register.pt', context=context.GeneralContext)
def register(request):
    form = forms.UserRegister(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        if registerCommon(request, form):
            return HTTPFound(location=request.route_url('user_wait_for_confirmation'))
    return {'form': form}


@view_config(route_name='user_register_other', renderer='muesli.web:templates/user/register_other.pt', context=context.GeneralContext)
def registerOther(request):
    form = forms.UserRegisterOther(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        if registerCommon(request, form):
            return HTTPFound(location=request.route_url('user_wait_for_confirmation'))
    return {'form': form}


def registerCommon(request, form):
    mails = request.db.query(models.User.email).all()
    mails = [m.email.lower() for m in mails]
    if form['email'].lower() in mails:
        request.session.flash('Ein Benutzer mit dieser E-Mail-Adresse existiert bereits.', queue='messages')
        return False
    else:
        user = models.User()
        form.obj = user
        form.saveValues()
        request.db.add(user)
        confirmation = models.Confirmation()
        confirmation.source = 'user/register'
        confirmation.user = user
        request.db.add(confirmation)
        request.db.commit()
        send_confirmation_mail(request, user, confirmation)
        return True

def send_confirmation_mail(request, user, confirmation):
    body = """
Hallo!

Sie haben sich bei MÜSLI mit den folgenden Daten angemeldet:

Name:   %s
E-Mail: %s

Um die Anmeldung abzuschließen, gehen Sie bitte auf die Seite

%s

Haben Sie sich nicht selbst angemeldet, ignorieren Sie diese Mail bitte
einfach.

Mit freudlichen Grüßen,
Das MÜSLI-Team
    """ % (user.name(), user.email, request.route_url('user_confirm', confirmation=confirmation.hash))
    message = Message(subject='MÜSLI: Ihre Registrierung bei MÜSLI',
                      sender=('%s <%s>' % (request.config['contact']['name'],
                                           request.config['contact']['email'])),
                      to=[user.email],
                      body=body)
    sendMail(message)


@view_config(route_name='user_wait_for_confirmation', renderer='muesli.web:templates/user/wait_for_confirmation.pt', context=context.GeneralContext)
def waitForConfirmation(request):
    return {}


@view_config(route_name='user_resend_confirmation_mail', renderer='muesli.web:templates/user/wait_for_confirmation.pt', context=context.UserContext)
def resendConfirmationMail(request):
    user_id = request.matchdict['user_id']
    confirmation = request.db.query(models.Confirmation).filter(models.Confirmation.user_id == user_id).first()
    user = confirmation.user
    body = """
Hallo!

Sie haben sich am %s bei MÜSLI mit den folgenden Daten angemeldet:

Name:   %s
E-Mail: %s

Um die Anmeldung abzuschließen, gehen Sie bitte auf die Seite

%s

Haben Sie sich nicht selbst angemeldet, ignorieren Sie diese Mail bitte
einfach.

Mit freudlichen Grüßen,
Das MÜSLI-Team
    """ % (confirmation.created_on, user.name(), user.email, request.route_url('user_confirm', confirmation=confirmation.hash))
    message = Message(subject='MÜSLI: Ihre Registrierung bei MÜSLI',
                      sender=('%s <%s>' % (request.config['contact']['name'],
                                           request.config['contact']['email'])),
                      to=[user.email],
                      body=body)
    sendMail(message)
    return {}


@view_config(route_name='user_confirm', renderer='muesli.web:templates/user/confirm.pt', context=context.ConfirmationContext)
def confirm(request):
    form = forms.UserConfirm(request, request.context.confirmation)
    if request.method == 'POST' and form.processPostData(request.POST):
        user = request.context.confirmation.user
        user.password = sha1(form['password'].encode('utf-8')).hexdigest()
        request.db.delete(request.context.confirmation)
        request.db.commit()
        return HTTPFound(location=request.route_url('user_login'))
    #       registerCommon(request, form)
    #       return HTTPFound(location=request.route_url('user_wait_for_confirmation'))
    return {'form': form,
            'confirmation': request.context.confirmation}


@view_config(route_name='user_change_email', renderer='muesli.web:templates/user/change_email.pt', context=context.GeneralContext, permission='change_email')
def changeEmail(request):
    form = forms.UserChangeEmail(request, request.user)
    if request.method == 'POST' and form.processPostData(request.POST):
        email = form['email']
        if request.db.query(models.User).filter(models.User.email == email).count() > 0:
            request.session.flash('Die Adresse "%s" kann nicht verwendet werden' % email, queue='messages')
        else:
            confirmation = models.Confirmation()
            confirmation.source = 'user/change_email'
            confirmation.user = request.user
            confirmation.what = email
            body = """
Hallo!

Sie haben bei MÜSLI Ihre E-Mail-Adresse geändert.

Neue Adresse: %s

Um die Änderung zu bestätigen, gehen Sie bitte auf die Seite

%s

Möchten Sie die Adresse doch nicht ändern, so ignorieren Sie diese Mail bitte
einfach.

Mit freundlichen Grüßen,
Das MÜSLI-Team
            """ % (email, request.route_url('user_confirm_email', confirmation=confirmation.hash))
            message = Message(subject='MÜSLI: E-Mail-Adresse ändern',
                              sender=('%s <%s>' % (request.config['contact']['name'],
                                                   request.config['contact']['email'])),
                              to=[email],
                              body=body)
            # As we are not using transactions,
            # we send the mail immediately.
            request.db.add(confirmation)
            request.db.commit()
            sendMail(message)
            # registerCommon(request, form)
            return HTTPFound(location=request.route_url('user_change_email_wait_for_confirmation'))
    return {'form': form}


@view_config(route_name='user_change_email_wait_for_confirmation', renderer='muesli.web:templates/user/change_email_wait_for_confirmation.pt', context=context.GeneralContext)
def changeEmailWaitForConfirmation(request):
    return {}


@view_config(route_name='user_confirm_email', renderer='muesli.web:templates/user/confirm_email.pt', context=context.ConfirmationContext)
def confirmEmail(request):
    done = False
    aborted = False
    if request.context.confirmation.source != 'user/change_email':
        return HTTPForbidden('This confirmation is not for a email change')
    if request.POST.get('confirm'):
        user = request.context.confirmation.user
        user.email = request.context.confirmation.what
        request.db.delete(request.context.confirmation)
        request.db.commit()
        done = True
    elif request.POST.get('abort'):
        request.db.delete(request.context.confirmation)
        aborted = True
        request.db.commit()
    #       registerCommon(request, form)
    #       return HTTPFound(location=request.route_url('user_wait_for_confirmation'))
    return {'done': done,
            'aborted': aborted,
            'confirmation': request.context.confirmation}


@view_config(route_name='user_change_password', renderer='muesli.web:templates/user/change_password.pt', context=context.GeneralContext, permission='change_password')
def changePassword(request):
    form = forms.UserChangePassword(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        request.user.password = sha1(form['new_password'].encode('utf-8')).hexdigest()
        request.session.flash('Neues Passwort gesetzt', queue='messages')
        request.db.commit()
    return {'form': form}


@view_config(route_name='user_reset_password', renderer='muesli.web:templates/user/reset_password.pt', context=context.GeneralContext)
def resetPassword(request):
    form = forms.UserResetPassword(request)
    if request.method == 'POST' and form.processPostData(request.POST):
        user = request.db.query(models.User).filter(models.User.email == form['email']).first()
        if not user:
            request.session.flash('User not found', queue='errors')
        else:
            confirmation = models.Confirmation()
            confirmation.user = user
            confirmation.source = 'user/reset_password'
            body = """
Hallo!

Um Ihr Passwort bei MÜSLI zurückzusetzen besuchen Sie bitte die Seite

%s

Haben Sie nicht selbst versucht Ihr Passwort zurückzusetzen, ignorieren Sie
diese Mail bitte einfach.

Mit freundlichen Grüßen,
Das MÜSLI-Team

            """ % (request.route_url('user_reset_password3', confirmation=confirmation.hash))
            message = Message(subject='MÜSLI: Passwort zurücksetzen',
                              sender=('%s <%s>' % (request.config['contact']['name'],
                                                   request.config['contact']['email'])),
                              to=[user.email],
                              body=body)
            # As we are not using transactions,
            # we send the mail immediately.
            request.db.add(confirmation)
            request.db.commit()
            sendMail(message)
            return HTTPFound(location=request.route_url('user_reset_password2'))
    return {'form': form}


@view_config(route_name='user_reset_password2', renderer='muesli.web:templates/user/reset_password2.pt', context=context.GeneralContext)
def resetPassword2(request):
    return {}


@view_config(route_name='user_reset_password3', renderer='muesli.web:templates/user/reset_password3.pt', context=context.ConfirmationContext)
def resetPassword3(request):
    form = forms.UserResetPassword3(request, request.context.confirmation)
    if request.method == 'POST' and form.processPostData(request.POST):
        user = request.context.confirmation.user
        user.password = sha1(form['password'].encode('utf-8')).hexdigest()
        request.db.delete(request.context.confirmation)
        request.db.commit()
        return HTTPFound(location=request.route_url('user_login'))
    #       registerCommon(request, form)
    #       return HTTPFound(location=request.route_url('user_wait_for_confirmation'))
    return {'form': form,
            'confirmation': request.context.confirmation}

@view_config(route_name='user_api_keys',
             renderer='muesli.web:templates/user/api_keys.pt',
             context=context.GeneralContext,
             permission='view_keys')
def list_auth_keys(request):
    form = forms.SetAuthCodeDescription(request)
    jwt_token = ""
    if request.method == 'POST' and form.processPostData(request.POST):
        exp = datetime.timedelta(days=muesli.config["api"]["key_expiration"])
        token = models.BearerToken(client="Personal Token",
                                   user=request.user,
                                   description=form['description'],
                                   expires=datetime.datetime.utcnow()+exp
                                  )
        request.db.add(token)
        request.db.flush()
        jwt_token = request.create_jwt_token(request.user.id,
                                             admin=(request.user.is_admin),
                                             jti=token.id,
                                             expiration=exp)
        request.session.flash("Ihr API Token wurde erstellt!", queue='messages')
        request.db.commit()
    tokens = (request.db.query(models.BearerToken)
                 .filter_by(user_id=request.user.id).filter(models.BearerToken.revoked == False).all())
    for token in tokens:
        token.expires = token.expires.strftime("%d. %B %Y, %H:%M Uhr")
        if not token.description:
            token.description = "Keine Beschreibung"
    if not tokens:
        tokens = ""
    return {'code': tokens,
            'form': form,
            'freshtoken': jwt_token}


@view_config(route_name='remove_api_key', context=context.GeneralContext)
def removeKey(request):
    code_id = int(request.matchdict['key_id'])
    #  TODO check if api_key.user_id matches user_id??
    api_key = request.db.query(models.BearerToken).get(code_id)
    if not api_key:
        request.session.flash('API Key nicht gefunden', queue='errors')
    else:
        api_key.revoked = True
        request.db.add(api_key)
        request.db.commit()
        request.session.flash('API Key entfernt ', queue='messages')
    if request.referrer:
        return HTTPFound(location=request.referrer)
    else:
        return HTTPFound(location=request.route_url('start'))


@view_config(route_name='user_ajax_complete', renderer='muesli.web:templates/user/ajax_complete.pt', context=context.TutorialContext, permission='viewOverview')
def ajaxComplete(request):
    search_str = request.POST['name']+'%'
    lecture_students = request.context.lecture.lecture_students_for_tutorials(tutorials=request.context.tutorials)
    lecture_students = lecture_students.filter(or_((func.lower(models.User.first_name).like(func.lower(search_str))),
                                                   (func.lower(models.User.last_name).like(func.lower(search_str))),
                                                   (func.lower(models.User.email).like(func.lower(search_str)))))
    students = [ls.student for ls in lecture_students]
    return {'users': students}
