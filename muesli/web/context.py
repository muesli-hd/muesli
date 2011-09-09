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

class GeneralContext(object):
  def __init__(self, request):
    self.__acl__ = [
        (Allow, 'group:administrators', ALL_PERMISSIONS),
        ]

class LectureContext(object):
  def __init__(self, request):
    lecture_id = request.matchdict['lecture_id']
    self.lecture = request.db.query(Lecture).get(lecture_id)
    self.__acl__ = [
		(Allow, Authenticated, 'view'),
        (Allow, 'user:{0}'.format(self.lecture.assistant_id), ('view', 'edit', 'view_tutorials')),
        (Allow, 'group:administrators', ALL_PERMISSIONS),
        ]+[(Allow, 'user:{0}'.format(tutor.id), ('view', 'take_tutorial', 'view_tutorials')) for tutor in self.lecture.tutors]

class TutorialContext(object):
  def __init__(self, request):
    tutorial_ids = request.matchdict['tutorial_ids']
    self.tutorials = [request.db.query(Tutorial).get(tutorial_id) for tutorial_id in tutorial_ids.split(',')]
    self.__acl__ = [
        (Allow, 'user:{0}'.format(self.tutorials[0].lecture.assistant_id), ('view', 'edit')),
        (Allow, 'group:administrators', ALL_PERMISSIONS),
        ]+[(Allow, 'user:{0}'.format(tutor.id), ('view')) for tutorial in self.tutorials for tutor in tutorial.lecture.tutors]
