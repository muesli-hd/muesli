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

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.url import route_url
from sqlalchemy.orm import exc
import sqlalchemy

import re
import os

@view_config(route_name='lecture_list', renderer='muesli.web:templates/lecture/list.pt')
class List(object):
	def __init__(self, request):
		self.request = request
		self.session = self.request.session
	def __call__(self):
		lectures = self.session.query(models.Lecture).all()
		return {'lectures': lectures}

@view_config(route_name='lecture_view', renderer='muesli.web:templates/lecture/view.pt')
class View(object):
	def __init__(self, request):
		self.request = request
		self.db = self.request.db
		self.lecture_id = request.matchdict['lecture_id']
	def __call__(self):
		lecture = self.db.query(models.Lecture).get(self.lecture_id)
		if lecture.mode == "prefs":
			times = self.db.query(sqlalchemy.func.sum(models.Tutorial.max_students), models.Tutorial.time).\
				filter(models.Tutorial.lecture == lecture).\
				group_by(models.Tutorial.time)
			times = [{'weekday':   utils.tutorialtimeToWeekday(result[1]),
				'timeofday': utils.tutorialtimeToTime(result[1]),
				'time':      result[1],
				'max_students': result[0]} for result in times]
			for time in times:
				time['penalty'] = 100
		else:
			times = []
		return {'lecture': lecture,
		        'times': times}