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

def tutorialtimeToTime(tutorialtime):
	return tutorialtime[1:]

def tutorialtimeToWeekday(tutorialtime):
	return tutorialtime[0]

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
