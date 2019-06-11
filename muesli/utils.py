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
from collections import defaultdict
import yaml

from muesli.types import Term

import muesli

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


modes = [['off', 'Keine Anmeldung'],
        ['direct', 'Direkte Anmeldung'],
        ['prefs', 'Praeferenzen'],
        ['static', 'Weder An- noch Abmeldung']]

categories = [{'id': 'assignment', 'name': 'Übungszettel'},
        {'id': 'exam', 'name': 'Klausur'},
        {'id': 'practical_assignment', 'name': 'Praktische Übung'},
        {'id': 'presence_assignment', 'name': 'Präsenzübung'},
        {'id': 'mock_exam', 'name': 'Probeklausur'}]

class Configuration:
    def __init__(self, filename):
        with open(filename, 'r') as config_file:
            self.data = yaml.safe_load(config_file.read())

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default):
        return self.data.get(key, default)


#TutorRights:
editAllTutorials = 'editAllTutorials'
editOwnTutorials = 'editOwnTutorial'
editNoTutorials = 'editNoTutorial'

tutorRights = [[editAllTutorials, 'Punkte zu allen Tutorien eintragen'],
                                        [editOwnTutorials, 'Punkte zu eigenen Tutorien eintragen'],
                                        [editNoTutorials, 'Keine Punkte eintragen']]

def getSubjects(user=None):
    hisSubjects = list(muesli.config['subjects'])
    if user and not user.subject in hisSubjects:
        hisSubjects.append(user.subject)
    hisSubjects = list(zip(hisSubjects,hisSubjects))
    return hisSubjects

def getSemesterLimit():
    now = datetime.datetime.now()
    semesterlimit = now.year
    if now.month < 4:
        semesterlimit -= 1
    term = '1' if now.month>=4 and now.month <=9 else '2'
    semesterlimit = '%4i%s' % (semesterlimit, term)
    return semesterlimit

def getTerms():
    first_term = muesli.config['terms']['first_term']
    terms_per_year = muesli.config['terms']['terms_per_year']

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
            return self.user in lecture.tutors
        else: return False
    def is_tutor_of_tutorials(self, tutorials):
        if self.is_loggedin():
            return all(self.user == tutorial.tutor for tutorial in tutorials)
        else:
            return False

def listStrings(strings):
    if len(strings)==0:
        return ''
    elif len(strings) == 1:
        return strings[0]
    else:
        part1 = strings[:-1]
        part2 = strings[-1]
        return ', '.join(part1)+' und '+part2

class DictOfObjects:
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

#From http://blogs.fluidinfo.com/terry/2012/05/26/autovivification-in-python-nested-defaultdicts-with-a-specific-final-type/
def autovivify(levels=1, final=dict):
    return (defaultdict(final) if levels < 2 else
            defaultdict(lambda: autovivify(levels - 1, final)))
