from muesli.models import *
from pyramid.security import Allow, Deny, Everyone, Authenticated, DENY_ALL, ALL_PERMISSIONS

class UserContext(object):
  def __init__(self, request):
    user_id = request.matchdict['user_id']
    self.user = request.db.query(User).get(user_id)
    self.__acl__ = [
        (Allow, 'user:{0}'.format(user_id), ('view', 'edit')),
        (Allow, 'group:administrators', ALL_PERMISSIONS),
        ]

class LectureContext(object):
  def __init__(self, request):
    lecture_id = request.matchdict['lecture_id']
    self.lecture = request.db.query(Lecture).get(lecture_id)
    self.__acl__ = [
		(Allow, Authenticated, 'view'),
        (Allow, 'user:{0}'.format(self.lecture.assistant_id), ('view', 'edit')),
        (Allow, 'group:administrators', ALL_PERMISSIONS),
        ]+[(Allow, 'user:{0}'.format(tutor.id), ('view', 'take')) for tutor in self.lecture.tutors]