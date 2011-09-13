# -*- coding: utf-8 -*-
#
# muesli/web/forms.py
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

import formencode
from formencode import validators

from muesli import models
from muesli import utils

def boolToValue(boolean):
	if boolean==True:
		return 1
	elif boolean==False:
		return 0
	elif boolean==None:
		return 'None'

def valueToBool(value):
	if value==1:
		return True
	if value==0:
		return False
	if value=='None':
		return None

class FormField(object):
	def __init__(self, name, label="", type="text", options=None, value=None, size=40, comment=None, validator=None, required=False):
		self.name = name
		self.label = label
		self.type = type
		self.options = options
		self.value = value
		self.size = size
		self.comment = comment
		self.validator = validator
		self.required = required

class Form(object):
	def __init__(self, formfields, send="Senden"):
		self.formfields = formfields
		self.updateNames()
		self.createSchema()
		self.errors = {}
		self.send=send
		self.message=""
	def createSchema(self):
		fields = self.formfields
		class Schema(formencode.Schema):
			def __init__(self, *args, **kwargs):
				for field in fields:
					if field.validator:
						kwargs[field.name] = field.validator
					else:
						kwargs[field.name] = formencode.validators.UnicodeString()
					kwargs[field.name].not_empty = field.required
				formencode.Schema.__init__(self, *args, **kwargs)
		self.formValidator = FormValidator(Schema())
	def updateNames(self):
		self.named_fields = {}
		for field in self.formfields:
			self.named_fields[field.name] = field
	def processPostData(self, postData):
		if self.formValidator.validate(postData):
			self.values = {}
			for name in self.named_fields:
				field = self.named_fields[name]
				if field.type in ['select', 'radio']:
					for option in field.options:
						if self.formValidator[name] == str(option[0]):
							field.value = option[0]
				else:
					field.value = self.formValidator[name]
				self.values[name] = field.value
			self.errors = self.formValidator.errors
			return True
		else:
			self.errors = self.formValidator.errors
			return False
	__getitem__ = lambda self, key: self.named_fields[key].value
	def __setitem__(self, key, value):
		self.named_fields[key].value=value

class FormValidator(object):
	def __init__(self, schema, obj=None, fields=[]):
		self.schema = schema
		self.value = {}
		if obj is not None:
			for f in fields:
				self.value[f] = getattr(obj, f)
	def validate(self, value):
		self.errors = {}
		try:
			self.value.update(self.schema.to_python(value))
			return True
		except formencode.Invalid as exc:
			self.errors = exc.unpack_errors()
		#for key, e in exc.error_dict.iteritems():
		#  self.errors[key] = e.msg
		#self.errors = exc.error_dict
			return False
	__getitem__ = lambda self, key: self.value.get(key, "")
	__contains__ = lambda self, key: key in self.value
	__iter__ = lambda self: self.value.iterkeys()
	iterkeys = __iter__
	iteritems = lambda self: self.value.iteritems()
	update = lambda self, *args, **kwargs: self.value.update(*args, **kwargs)
	def bind(self, obj, fields):
		"""
		Update fields in obj using submitted values.
		"""
		for f in fields:
			setattr(obj, f, self[f])

class ObjectForm(Form):
	def __init__(self, obj, formfields, send="Ändern"):
		Form.__init__(self, formfields, send=send)
		self.obj = obj
	def saveField(self, fieldName):
		setattr(self.obj, fieldName, self[fieldName])
	def saveValues(self):
		for name in self.named_fields:
			self.saveField(name)


class UserLogin(formencode.Schema):
	email = validators.String(not_empty=True)
	password = validators.String(not_empty=True)

class LectureEdit(ObjectForm):
	def __init__(self, request, lecture):
		self.request =  request
		formfields = [
			FormField('type',
			   label='Typ',
			   type='select',
			   options=[[type, utils.lecture_types[type]['name']] for type in utils.lecture_types],
			   value=lecture.type,
			   required=True),
			FormField('name',
			   label='Name',
			   type='text',
			   size=100,
			   value=lecture.name,
			   required=True),
			FormField('term',
			   label='Semester',
			   type='select',
			   options=utils.getTerms(),
			   value=lecture.term),
			FormField('lsf_id',
			   label='Veranstaltungsnummer',
			   type='text',
			   size=20,
			   value=lecture.lsf_id),
			FormField('lecturer',
			   label='Dozent',
			   type='text',
			   size=40,
			   value=lecture.lecturer),
			FormField('url',
			   label='Homepage',
			   size=100,
			   value=lecture.url),
			FormField('mode',
			   label='Anmeldemodus',
			   type='select',
			   options=utils.modes,
			   value=lecture.mode),
			FormField('minimum_preferences',
			   label=u'Minimum möglicher Termine',
			   size=5,
			   comment=u'Bei Präferenzenanmeldung: Studenten müssen mindestens an soviel Terminen können. (Leer: Defaultformel)',
			   value=lecture.minimum_preferences,
			   validator=validators.Int()),
			FormField('password',
			   label=u'Passwort für Übungsleiter',
			   size=40,
			   comment=u'Bei leerem Passwort keine Anmeldung als Übungsleiter möglich',
			   value=lecture.password),
			FormField('is_visible',
			   label='Sichtbar',
			   type='radio',
			   options=[[1, 'Ja'], [0, 'Nein']],
			   value=boolToValue(lecture.is_visible))
			]
		if request.permissionInfo.has_permission('change_assistant'):
			assistants = request.db.query(models.User).filter(models.User.is_assistant==1).all()
			formfields.append(
			  FormField('assistant',
			   label='Assistent',
			   type='select',
			   options=[[a.id, a.name()] for a in assistants],
			   value=lecture.assistant.id,
			   required=True,
			   validator=validators.Int()))
		ObjectForm.__init__(self, lecture, formfields, send=u'Ändern')
	def saveField(self, fieldName):
		if fieldName == 'is_visible':
			self.obj.is_visible = valueToBool(self['is_visible'])
		elif fieldName == 'assistant':
			assistant = self.request.db.query(models.User).get(self['assistant'])
			self.obj.assistant = assistant
		else:
			ObjectForm.saveField(self, fieldName)

class UserEdit(ObjectForm):
	def __init__(self, request, user):
		formfields = [
			FormField('email',
			   label='E-Mail', size=40,
			   value=user.email,
			   required=True,
			   validator=validators.Email()),
			FormField('title',
			   label='Titel', size=20,
			   value=user.title),
			FormField('first_name',
			   label='Vorname', size=40,
			   value=user.first_name,
			   required=True),
			FormField('last_name',
			   label='Nachname', size=40,
			   value=user.last_name,
			   required=True),
			FormField('matrikel',
			   label='Matrikelnummer', size=10,
			   value=user.matrikel),
			FormField('subject',
			   label='Studiengang',
			   type='select',
			   value=user.subject,
			   options=utils.getSubjects(user)),
			FormField('subject_alt',
			   label='Studiengang', size=30, comment=u'Genauer Studiengang (falls Sonstiges gewählt)',
			   value=''),
			FormField('birth_date',
			   label='Geburtstag', size=10, comment='(TT.MM.JJJJ)',
			   value=user.birth_date),
			FormField('birth_place',
			   label='Geburtsort', size=20,
			   value=user.birth_place),
			FormField('is_assistant',
			   label='Assistent',
			   type='radio',
			   options=[[1, 'Ja'], [0, 'Nein']],
			   value=1 if user.is_assistant else 0),
			FormField('is_admin',
			   label='Admin',
			   type='radio',
			   options=[[1, 'Ja'], [0, 'Nein']],
			   value=1 if user.is_admin else 0)
			]
		ObjectForm.__init__(self, user, formfields, send=u'Änderungen übernehmen')
	def saveField(self, fieldName):
		if fieldName == 'subject':
			if self['subject']=='Sonstiges':
				self.obj.subject = self['subject_alt']
			else:
				self.obj.subject = self['subject']
		elif fieldName == 'alt_subject':
			pass
		else:
			ObjectForm.saveField(self, fieldName)

class LectureAddExam(ObjectForm):
	def __init__(self, request):
		formfields = [
			FormField('name',
			   label='Name', size=100,
			   required=True),
			FormField('category',
			   label='Kategorie',
			   type='select',
			   options=[[cat['id'], cat['name']] for cat in utils.categories]),
			FormField('url',
			   label='URL', size=100)
			]
		ObjectForm.__init__(self, None, formfields, send=u'Anlegen')

class LectureEditExam(ObjectForm):
	def __init__(self, request, exam):
		formfields = [
			FormField('name',
			   label='Name', size=100,
			   value=exam.name,
			   required=True),
			FormField('category',
			   label='Kategorie',
			   type='select',
			   value=exam.category,
			   options=[[cat['id'], cat['name']] for cat in utils.categories]),
			FormField('url',
			   value=exam.url,
			   label='URL', size=100),
			FormField('admission',
			   label='Zulassung',
			   type='radio',
			   value=boolToValue(exam.admission),
			   options=[[1, 'Editieren erlaubt'], [0, 'Editieren gesperrt'], ['None', 'Nicht notwendig']]),
			FormField('registration',
			   label='Anmeldung',
			   type='radio',
			   value=boolToValue(exam.registration),
			   options=[[1, 'Editieren erlaubt'], [0, 'Editieren gesperrt'], ['None', 'Nicht notwendig']]),
			]
		ObjectForm.__init__(self, exam, formfields, send=u'Änderungen speichern')
	def saveField(self, fieldName):
		if fieldName in ['admission', 'registration']:
			setattr(self.obj, fieldName, valueToBool(self[fieldName]))
		else:
			ObjectForm.saveField(self, fieldName)

class TutorialAdd(ObjectForm):
	def __init__(self, request):
		# TODO: Übungsleiter angeben. Aber wurde das jemals genutzt?
		formfields = [
			#FormField('tutor',
			#   label=u'Übungsleiter', size=64),
			FormField('place',
			   label='Ort', size=64,
			   required=True),
			FormField('wday',
			   label='Wochentag',
			   type='select',
			   options=enumerate(['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']),
			   required=True),
			FormField('timeofday',
			   label='Uhrzeit', size=5,
			   comment='(HH:MM oder HH)',
			   validator=validators.Regex(r'^[012]?[0-9](:[0-5][0-9])?$'),
			   required=True),
			FormField('max_students',
			   label='Max. Teilnehmerzahl', size=5,
			   validator=validators.Int,
			   required=True),
			FormField('comment',
			   label='Kommentar', size=64),
			FormField('is_special',
			   label='Spezial',
			   type='radio',
			   value=0,
			   options=[[1, 'Ja'], [0, 'Nein']])
			]
		ObjectForm.__init__(self, None, formfields, send=u'Anlegen')
	def saveField(self, fieldName):
		if fieldName == 'is_special':
			setattr(self.obj, fieldName, valueToBool(self[fieldName]))
		elif fieldName == 'wday':
			pass
		elif fieldName == 'timeofday':
			timeofday = self['timeofday']
			if not ':' in timeofday:
				timeofday += ':00'
			if len(timeofday) <5:
				timeofday = '0' + timeofday
			timeString = '%s %s' % (self['wday'], timeofday)
			setattr(self.obj, 'time', timeString)
		else:
			ObjectForm.saveField(self, fieldName)

class ExamAddOrEditExercise(ObjectForm):
	def __init__(self, request, exercise):
		formfields = [
			FormField('nr',
			   label='Nr.', size=4,
			   value=exercise.nr if exercise else None,
			   required=True,
			   validator=validators.Int()),
			FormField('maxpoints',
			   label='Punkte', size=4,
			   value=exercise.maxpoints if exercise else None,
			   # TODO: Nur eine Nachkommastelle erlaubt
			   validator=validators.Number(min=0)),
			]
		ObjectForm.__init__(self, exercise, formfields, send=u'Anlegen/Ändern')