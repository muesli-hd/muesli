# utils.py
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

import datetime
import pyramid.security

preferences = [\
	{'penalty': 1, 'name': 'Gut'},
	{'penalty': 3, 'name': 'Mittel'},
	{'penalty': 10,'name': 'Schlecht'},
	{'penalty': 100, 'name': 'Gar nicht'}]

penalty_names = dict([[pref['penalty'], pref['name']] for pref in preferences])

def getSemesterLimit():
	now = datetime.datetime.now()
	semesterlimit = now.year
	if now.month < 3:
		semesterlimit -= 1
	term = '1' if now.month>=3 and now.month <=8 else '2'
	semesterlimit = '%4i%s' % (semesterlimit, term)
	return semesterlimit

class PermissionInfo:
	def __init__(self, request):
		self.request = request
	def has_permission(self, permission):
		return pyramid.security.has_permission(permission, self.request.context, self.request)

class UserInfo:
	def __init__(self, user):
		self.user = user
	def is_loggedin(self):
		return self.user != None
	def is_admin(self):
		if self.is_loggedin():
			return self.user.is_admin
		else: return False
	def is_assistant(self):
		if self.is_loggedin():
			return self.user.is_assistant
		else: return False
	def is_tutor(self, lecture):
		if self.is_loggedin():
			return self in lecture.tutors
		else: return False
