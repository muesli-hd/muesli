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

from muesli import models, utils
from muesli.web.forms import *
from muesli.web.context import *
from muesli.mail import Message, sendMail
from muesli.changelog import changelog as changelog_str

from pyramid import security
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPInternalServerError, HTTPFound
import pyramid.exceptions
from pyramid.url import route_url
from sqlalchemy.orm import exc, joinedload
from hashlib import sha1

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
	if request.GET.get('show_all', '0')=='0':
		semesterlimit = utils.getSemesterLimit()
		tutorials_as_tutor = tutorials_as_tutor.filter(Lecture.term >= semesterlimit)
		tutorials = tutorials.filter(Lecture.term >= semesterlimit)
		lectures_as_assistant = lectures_as_assistant.filter(Lecture.term >= semesterlimit)
	return {'time_preferences': request.user.prepareTimePreferences(),
	        'penalty_names': utils.penalty_names,
	        'tutorials_as_tutor': tutorials_as_tutor.all(),
	        'tutorials': tutorials.all(),
	        'lectures_as_assistant': lectures_as_assistant.all()}

@view_config(route_name='admin', renderer='muesli.web:templates/admin.pt', context=GeneralContext, permission='admin')
def admin(request):
	return {}

@view_config(route_name='contact', renderer='muesli.web:templates/contact.pt')
def contact(request):
	return {}

@view_config(route_name='index', renderer='muesli.web:templates/index.pt')
def index(request):
	return {}

@view_config(route_name='email_users', renderer='muesli.web:templates/email_users.pt', context=GeneralContext, permission='admin')
def emailUsers(request):
	ttype = request.params.get('type', 'wrong_subject')
	form = EmailWrongSubject(ttype)
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
	if request.method == 'POST' and form.processPostData(request.POST):
		message = Message(subject=form['subject'],
			sender=u'MÜSLI-Team <muesli@mathi.uni-heidelberg.de>',
			to= [],
			bcc=[s.email for s in bad_students],
			body=form['body'])
		if request.POST['attachments'] not in ['', None]:
			message.attach(request.POST['attachments'].filename, data=request.POST['attachments'].file)
		sendMail(message)
		request.session.flash('A Mail has been send to all students with wrong subject', queue='messages')
	return {'form': form,
	        'type': ttype,
	        'table': table,
	        'headers': headers,
	        'students': bad_students}

@view_config(context = Exception, renderer='muesli.web:templates/error.pt')
def internalServerError(exc, request):
	if not muesli.productive:
		print "TRYING TO RECONSTRUCT EXCEPTION"
		traceback.print_exc()
		print "RAISING ANYHOW"
		raise exc
	now = datetime.datetime.now()
	traceback.print_exc()
	email = request.user.email if request.user else '<nobody>'
	return {'now': now,
	        'email': email}
@view_config(route_name='changelog', renderer='muesli.web:templates/changelog.pt')
def changelog(request):
	entries = []
	for part in changelog_str.split('====')[1:]:
		date = part.split('\n',1)[0]
		text = []
		for line in part.split('\n')[1:]:
			if line.startswith('topic:'):
				pass
			elif line.startswith('concerns:'):
				pass
			else: text.append(line)
		text = u'\n'.join(text)
		entries.append({'date': date, 'description': text})
	return {'entries': entries}


@view_config(context=pyramid.exceptions.HTTPForbidden, renderer='muesli.web:templates/forbidden.pt')
def forbidden(exc, request):
	request.response.status=403
	return {}

