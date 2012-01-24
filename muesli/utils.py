# -*- coding: utf-8 -*-
#
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

import datetime
import pyramid.security

from muesli.types import Term

preferences = [\
	{'penalty': 1, 'name': 'Gut'},
	{'penalty': 3, 'name': 'Mittel'},
	{'penalty': 10,'name': 'Schlecht'},
	{'penalty': 100, 'name': 'Gar nicht'}]

penalty_names = dict([[pref['penalty'], pref['name']] for pref in preferences])

ghostpenalty = 20000
ghostcapacity = 10000
lpsolve = '/usr/bin/lp_solve'
students_unhappiness = 50

lecture_types={
	'lecture':
		 {'name':  'Vorlesung',
			'tutorial': u'Übungsgruppe',
			'tutorials': u'Übungsgruppen',
			'tutor':     u'Übungsleiter',
			'tutors':    u'Übungsleiter',
			'comment':   'Kommentar'},
	'seminar':
		 {'name':  'Seminar',
			'tutorial': u'Vortrag',
			'tutorials': u'Vorträge',
			'tutor':     u'Vortragender',
			'tutors':    u'Vortragende',
			'comment':   'Thema'},
	'modul':
		{'name':     'Modul',
			'tutorial': 'Veranstaltung',
			'tutorials': 'Veranstaltungen',
			'tutor':     'Dozent',
			'tutors':    'Dozenten',
			'comment':   'Titel'}
	}

modes = [['off', 'Keine Anmeldung'],
	['direct', 'Direkte Anmeldung'],
	['prefs', 'Praeferenzen'],
	['static', 'Weder An- noch Abmeldung']]

categories = [{'id': 'assignment', 'name': u'Übungszettel'},
	{'id': 'exam', 'name': 'Klausur'},
	{'id': 'presence_assignment', 'name': u'Präsenzübung'},
	{'id': 'mock_exam', 'name': 'Probeklausur'}]

subjects = [
	'Mathematik (BSc)',
	'Mathematik (MSc)',
	'Mathematik (Dipl.)',
	'Mathematik (LA) (Hauptfach)',
	'Mathematik (LA) (Beifach)',
	'Physik (BSc)',
	'Physik (MSc)',
	'Physik (Dipl.)',
	'Physik (LA)',
	'Angewandte Informatik (BSc)',
	'Anwendungsorientierte Informatik (MSc)',
	'Computerlinguistik (BA)',
	'Computerlinguistik (Magister)',
	'Medizinische Informatik (BSc)',
	'Medizinische Informatik (MSc)',
	'Medizinische Informatik (Dipl.)',
	'Sonstiges'
	]

def getSubjects(user=None):
	hisSubjects = list(subjects)
	if user and not user.subject in hisSubjects:
		hisSubjects.append(user.subject)
	hisSubjects = zip(hisSubjects,hisSubjects)
	return hisSubjects

def getSemesterLimit():
	now = datetime.datetime.now()
	semesterlimit = now.year
	if now.month < 3:
		semesterlimit -= 1
	term = '1' if now.month>=3 and now.month <=8 else '2'
	semesterlimit = '%4i%s' % (semesterlimit, term)
	return semesterlimit

def getTerms():
	first_term = 20082
	terms_per_year = 2

	now = datetime.datetime.now()
	year = now.year
	last_term = year * 10 + 11
	terms = []
	term = first_term
	while term < last_term:
		terms.append([Term(str(term)),Term(str(term))])
		if term % 10 >= terms_per_year:
			term = term + 11 - (term % 10)
		else:
			term += 1
	return terms

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

class DictOfObjects(object):
	def __init__(self, createFunction):
		self.d = {}
		self.createFunction=createFunction
	def __getitem__(self, key):
		if not key in self.d:
			self.d[key] = self.createFunction()
		return self.d[key]
	def __setitem__(self, key, value):
		self.d[key] = value
	def __iter__(self):
		return self.d.__iter__()
	def __str__(self):
		return "%r" % self.d

class AutoVivification(dict):
	"""Implementation of perl's autovivification feature.
	   from: http://stackoverflow.com/q/635483"""
	def __getitem__(self, item):
		try:
			return dict.__getitem__(self, item)
		except KeyError:
			value = self[item] = type(self)()
			return value
	def update(self, other):
		for key in other:
			if isinstance(other[key], dict):
				self[key].update(other[key])
			else: self[key] = other[key]
	def update_available(self, other):
		for key in other:
			if isinstance(other[key], dict):
				if key in self:
					if isinstance(other[key], AutoVivification):
						self[key].update_available(other[key])
					else:
						self[key].update(other[key])
			else: self[key] = other[key]

