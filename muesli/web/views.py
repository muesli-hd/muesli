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

from pyramid import security
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.url import route_url
from sqlalchemy.orm import exc
from hashlib import sha1

import re
import os

@view_config(route_name='overview', renderer='muesli.web:templates/overview.pt')
class Overview(object):
	def __init__(self, request):
		self.request = request
	def __call__(self):
		return {}

@view_config(route_name='start', renderer='muesli.web:templates/start.pt')
def start(request):
	tutorials_as_tutor = request.user.tutorials_as_tutor
	tutorials = request.user.tutorials
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
