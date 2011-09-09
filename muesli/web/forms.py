import formencode
from formencode import validators

class FormField(object):
	def __init__(self, name, label="", type="text", options=None, value=None, size=40, comment=None):
		self.name = name
		self.label = label
		self.type = type
		self.options = options
		self.value = value
		self.size = size
		self.comment = comment

class FormData(object):
	def __init__(self, formfields):
		self.formfields = formfields
		self.updateNames()
	def updateNames(self):
		self.named_fields = {}
		for field in self.formfields:
			self.named_fields[field.name] = field
	def processPostData(self, postData):
		self.values = {}
		for name in self.named_fields:
			field = self.named_fields[name]
			if field.type == 'radio':
				for option in field.options:
					if name+'_'+str(option[0]) in postData:
						field.value = option[0]
			elif field.type == 'select':
				for option in field.options:
					if postData[name] == str(option[0]):
						field.value = option[0]
			else:
				field.value = postData[name]
			self.values[name] = field.value
		#print self.values
	__getitem__ = lambda self, key: self.named_fields.get(key, None).value

class Form(object):
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

class UserLogin(formencode.Schema):
	email = validators.String(not_empty=True)
	password = validators.String(not_empty=True)

class LectureEdit(formencode.Schema):
	name = validators.String(not_empty=True)