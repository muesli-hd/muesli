import formencode
from formencode import validators

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
  email = validators.PlainText(not_empty=True)
  password = validators.String(not_empty=True)
