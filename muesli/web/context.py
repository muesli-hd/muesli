from muesli.models import *
from pyramid.security import Allow, Deny, Everyone, Authenticated, DENY_ALL, ALL_PERMISSIONS
from pyramid.httpexceptions import HTTPNotFound

class UserContext(object):
	def __init__(self, request):
		user_id = request.matchdict['user_id']
		self.user = request.db.query(User).get(user_id)
		if self.user is None:
			raise HTTPNotFound(detail='User not found')
		self.__acl__ = [
			(Allow, 'user:{0}'.format(user_id), ('view', 'edit')),
			(Allow, 'group:administrators', ALL_PERMISSIONS),
			]

class GeneralContext(object):
	def __init__(self, request):
		self.__acl__ = [
			(Allow, 'group:administrators', ALL_PERMISSIONS),
			]

class GradingContext(object):
	def __init__(self, request):
		grading_id = request.matchdict['grading_id']
		self.grading = request.db.query(Grading).get(grading_id)
		if self.grading is None:
			raise HTTPNotFound(detail='Grading not found')
		self.__acl__ = [
			(Allow, 'user:{0}'.format(self.grading.lecture.assistant_id), ('view', 'edit')),
			(Allow, 'group:administrators', ALL_PERMISSIONS),
			]


class LectureContext(object):
	def __init__(self, request):
		lecture_id = request.matchdict['lecture_id']
		self.lecture = request.db.query(Lecture).get(lecture_id)
		if self.lecture is None:
			raise HTTPNotFound(detail='Lecture not found')
		self.__acl__ = [
			(Allow, Authenticated, 'view'),
			(Allow, 'user:{0}'.format(self.lecture.assistant_id), ('view', 'edit', 'view_tutorials')),
			(Allow, 'group:administrators', ALL_PERMISSIONS),
			]+[(Allow, 'user:{0}'.format(tutor.id), ('view', 'take_tutorial', 'view_tutorials')) for tutor in self.lecture.tutors]

class TutorialContext(object):
	def __init__(self, request):
		tutorial_ids = request.matchdict.get('tutorial_ids', request.matchdict.get('tutorial_id', ''))
		self.tutorials = request.db.query(Tutorial).filter(Tutorial.id.in_(tutorial_ids.split(',')))
		if None in self.tutorials:
			raise HTTPNotFound(detail='Tutorial not found')
		self.__acl__ = [
			(Allow, 'user:{0}'.format(self.tutorials[0].lecture.assistant_id), ('view', 'edit')),
			(Allow, 'group:administrators', ALL_PERMISSIONS),
			]+[(Allow, 'user:{0}'.format(tutor.id), ('view')) for tutorial in self.tutorials for tutor in tutorial.lecture.tutors]

class ExamContext(object):
	def __init__(self, request):
		exam_id = request.matchdict['exam_id']
		self.exam = request.db.query(Exam).get(exam_id)
		if self.exam is None:
			raise HTTPNotFound(detail='Exam not found')
		self.__acl__ = [
			(Allow, Authenticated, 'view_points'),
			(Allow, 'user:{0}'.format(self.exam.lecture.assistant_id), ('view_points', 'edit', 'enter_points')),
			(Allow, 'group:administrators', ALL_PERMISSIONS),
			]+[(Allow, 'user:{0}'.format(tutor.id), ('view_points', 'enter_points')) for tutor in self.exam.lecture.tutors]
