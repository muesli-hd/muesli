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
from muesli.web.forms import *
from muesli.web.context import *

from pyramid import security
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPFound
from pyramid.url import route_url
from sqlalchemy.orm import exc
from hashlib import sha1

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message, Attachment

import re
import os

@view_config(route_name='user_login', renderer='muesli.web:templates/user/login.pt')
def login(request):
	form = FormValidator(UserLogin())
	if request.method == 'POST' and form.validate(request.POST):
		user = request.db.query(models.User).filter_by(email=form['email'], password=sha1(form['password']).hexdigest()).first()
		if user is not None:
			security.remember(request, user.id)
			request.user = user
			url = request.route_url('start')
			return HTTPFound(location=url)
	return { 'form': form, 'user': security.authenticated_userid(request) }

@view_config(route_name='user_logout')
def logout(request):
	security.forget(request)
	request.session.invalidate()
	return HTTPFound(location=request.route_url('index'))

@view_config(route_name='user_list', renderer='muesli.web:templates/user/list.pt', context=GeneralContext, permission='admin')
def list(request):
	users = request.db.query(models.User).order_by(models.User.last_name, models.User.first_name)
	return {'users': users}

@view_config(route_name='user_edit', renderer='muesli.web:templates/user/edit.pt', context=UserContext, permission='edit')
def edit(request):
	user_id = request.matchdict['user_id']
	user = request.db.query(models.User).get(user_id)
	form = UserEdit(request, user)
	if request.method == 'POST' and form.processPostData(request.POST):
		form.saveValues()
		request.db.commit()
	return {'user': user,
	        'form': form,
	        'time_preferences': user.prepareTimePreferences(),
	        'lectures_as_assistant': user.lectures_as_assistant.all(),
	        'tutorials_as_tutor': user.tutorials_as_tutor.all(),
	        'penalty_names': utils.penalty_names}

@view_config(route_name='user_update', renderer='muesli.web:templates/user/update.pt', context=GeneralContext, permission='update')
def update(request):
	form = UserUpdate(request, request.user)
	if request.method == 'POST' and form.processPostData(request.POST):
		form.saveValues()
		request.db.commit()
		request.session.flash(u'Angaben geändert', queue='messages')
	return {'form': form}

@view_config(route_name='user_register', renderer='muesli.web:templates/user/register.pt', context=GeneralContext)
def register(request):
	form = UserRegister(request)
	if request.method == 'POST' and form.processPostData(request.POST):
		registerCommon(request, form)
		return HTTPFound(location=request.route_url('user_wait_for_confirmation'))
	return {'form': form}

def registerCommon(request, form):
	if request.db.query(models.User).filter(models.User.email==form['email']).first():
		request.session.flash(u'Ein Benutzer mit dieser E-Mail-Adresse existiert bereits.', queue='messages')
		return
	else:
		user = models.User()
		form.obj = user
		form.saveValues()
		request.db.add(user)
		confirmation = models.Confirmation()
		confirmation.source = u'user/register'
		confirmation.user = user
		request.db.add(confirmation)
		send_confirmation_mail(request, user, confirmation)
		#request.db.commit()

def send_confirmation_mail(request, user, confirmation):
	mailer = get_mailer(request)
	body =u"""
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
	""" %(user.name(), user.email, request.route_url('user_confirm', confirmation=confirmation.hash))
	message = Message(subject=u'MÜSLI: Ihre Registrierung bei MÜSLI',
		sender=u'MÜSLI-Team <muesli@mathi.uni-heidelberg.de>',
		recipients=[user.email],
		body=body)
	# As we are not using transactions,
	# we send the mail immediately.
	mailer.send_immediately(message)

@view_config(route_name='user_wait_for_confirmation', renderer='muesli.web:templates/user/wait_for_confirmation.pt', context=GeneralContext)
def waitForConfirmation(request):
	return {}

@view_config(route_name='user_confirm', renderer='muesli.web:templates/user/confirm.pt', context=ConfirmationContext)
def confirm(request):
	form = UserConfirm(request, request.context.confirmation)
	if request.method == 'POST' and form.processPostData(request.POST):
		user = request.context.confirmation.user
		print form['password']
		user.password = sha1(form['password']).hexdigest()
		request.db.delete(request.context.confirmation)
		request.db.commit()
		return HTTPFound(location=request.route_url('user_login'))
	#	registerCommon(request, form)
	#	return HTTPFound(location=request.route_url('user_wait_for_confirmation'))
	return {'form': form,
	        'confirmation': request.context.confirmation}
