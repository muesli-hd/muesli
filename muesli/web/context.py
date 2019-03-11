from muesli.web.navigation_tree import *
from muesli.models import *
from pyramid.security import Allow, Deny, Everyone, Authenticated, DENY_ALL, ALL_PERMISSIONS
from pyramid.httpexceptions import HTTPNotFound, HTTPForbidden

from sqlalchemy import and_

from muesli.utils import editAllTutorials, editOwnTutorials, editNoTutorials

def getTutorials(request):
    """returns tutorials and tutorial_ids for this request.
    Does also a check whether the tutorials belong to the same lecture."""
    tutorial_ids = request.matchdict.get('tutorial_ids', request.matchdict.get('tutorial_id', '')).split(',')
    if len(tutorial_ids)==1 and tutorial_ids[0]=='':
        tutorial_ids = []
        tutorials = []
    else:
        tutorials = request.db.query(Tutorial).filter(Tutorial.id.in_(tutorial_ids)).all()
    checkTutorials(tutorials)
    return tutorials, tutorial_ids

def checkTutorials(tutorials):
    if tutorials:
        lecture_id = tutorials[0].lecture_id
        for tutorial in tutorials:
            if tutorial.lecture_id != lecture_id:
                raise HTTPForbidden('Tutorials belong to different lectures!')

def getTutorForTutorials(tutorials):
    if tutorials:
        tutorlist = [set([tutorial.tutor]) for tutorial in tutorials if tutorial.tutor]
        if tutorlist:
            tutors = set.intersection(*tutorlist)
            return tutors
        else:
            return []
    else:
        return []

class UserContext:
    def __init__(self, request):
        user_id = request.matchdict['user_id']
        self.user = request.db.query(User).get(user_id)
        if self.user is None:
            raise HTTPNotFound(detail='User not found')
        self.__acl__ = [
                (Allow, 'user:{0}'.format(user_id), ('view')),
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]

class ConfirmationContext:
    def __init__(self, request):
        confirmation_hash = request.matchdict['confirmation']
        self.confirmation = request.db.query(Confirmation).get(confirmation_hash)
        if self.confirmation is None:
            raise HTTPNotFound(detail='Confirmation not found')
        self.__acl__ = [
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]

class NonLoginContext:
    def __init__(self, request):
        self.__acl__ = [
            (Allow, Everyone, ('view')),
            (Allow, 'group:administrators', ALL_PERMISSIONS)
        ]

class GeneralContext:
    def __init__(self, request):
        self.__acl__ = [
                (Allow, Authenticated, ('update', 'change_email', 'change_password','view_keys','remove_keys')),
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]+[(Allow, 'user:{0}'.format(a.id), 'create_lecture') for a in request.db.query(User).filter(User.is_assistant==1).all()]

class GradingContext:
    def __init__(self, request):
        grading_id = request.matchdict['grading_id']
        self.grading = request.db.query(Grading).get(grading_id)
        if self.grading is None:
            raise HTTPNotFound(detail='Grading not found')
        self.__acl__ = [
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]+[(Allow, 'user:{0}'.format(assistant.id), ('view', 'edit')) for assistant in self.grading.lecture.assistants]


class LectureContext:
    def __init__(self, request):
        lecture_id = request.matchdict['lecture_id']
        self.lecture = request.db.query(Lecture).get(lecture_id)
        if self.lecture is None:
            raise HTTPNotFound(detail='Lecture not found')
        self.__acl__ = [
                (Allow, Authenticated, ('view', 'view_own_points', 'add_tutor')),
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]+[(Allow, 'user:{0}'.format(assistant.id), ('view', 'edit','change_assistant', 'view_tutorials', 'get_tutorials', 'mail_tutors')) for assistant in self.lecture.assistants
                ]+[(Allow, 'user:{0}'.format(tutor.id), ('view', 'take_tutorial', 'view_tutorials', 'get_tutorials', 'mail_tutors')) for tutor in self.lecture.tutors]

        # add lecture specific links
        if self.lecture is None:
            return

        if request.has_permission('edit', self):
            lecture_root = NavigationTree("Aktuelle Vorlesung",
                    request.route_url('lecture_edit', lecture_id=self.lecture.id))
        else:
            lecture_root = NavigationTree("Aktuelle Vorlesung",
                    request.route_url('lecture_view', lecture_id=self.lecture.id))
        nodes = get_lecture_specific_nodes(request, self, self.lecture.id)
        for node in nodes:
            lecture_root.append(node)

        if lecture_root.children:
            request.navigationTree.prepend(lecture_root)

class TutorialContext:
    def __init__(self, request):
        self.tutorial_ids_str = request.matchdict.get('tutorial_ids', request.matchdict.get('tutorial_id', ''))
        self.tutorials, self.tutorial_ids = getTutorials(request)
        if self.tutorials:
            self.lecture = self.tutorials[0].lecture
        else:
            lecture_id = request.matchdict.get('lecture_id', None)
            if lecture_id:
                self.lecture = request.db.query(Lecture).get(lecture_id)
            else:
                self.lecture = None
        self.__acl__ = [
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]
        if self.lecture:
            self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('viewOverview', 'take_tutorial', 'mail_tutors')) for tutor in self.lecture.tutors]
            self.__acl__ += [((Allow, 'user:{0}'.format(assistant.id), ('viewOverview', 'viewAll', 'sendMail', 'edit', 'remove_student'))) for assistant in self.lecture.assistants]
        if self.tutorials:
            if self.lecture.tutor_rights == editOwnTutorials:
                self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('viewAll', 'remove_student')) for tutor in getTutorForTutorials(self.tutorials)]
            elif self.lecture.tutor_rights == editNoTutorials:
                #TODO: This has to be a bug?!
                self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('viewAll', 'remove_student')) for tutor in getTutorForTutorials(self.tutorials)]
            elif self.lecture.tutor_rights == editAllTutorials:
                self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('viewAll', 'remove_student')) for tutor in self.lecture.tutors]
            else: raise ValueError('Tutorrights %s not known' % self.lecture.tutor_rights)
            for tutor in getTutorForTutorials(self.tutorials):
                self.__acl__.append((Allow, 'user:{0}'.format(tutor.id), ('sendMail')))
            if self.tutorials[0].lecture.mode == 'direct':
                self.__acl__.append((Allow, Authenticated, ('subscribe')))
            if self.tutorials[0].lecture.mode in ['direct', 'off']:
                self.__acl__.append((Allow, Authenticated, ('unsubscribe')))

        # add tutorial specific links
        if self.lecture is None:
            return

        if request.has_permission('edit', self):
            lecture_root = NavigationTree("Aktuelle Vorlesung",
                    request.route_url('lecture_edit', lecture_id=self.lecture.id))
        else:
            lecture_root = NavigationTree("Aktuelle Vorlesung",
                    request.route_url('lecture_view', lecture_id=self.lecture.id))
        nodes = get_lecture_specific_nodes(request, self, self.lecture.id)
        for node in nodes:
            lecture_root.append(node)

        for tutorial in self.tutorials:
            tutorial_root = NavigationTree("Aktuelles Tutorial", request.route_url('tutorial_view', tutorial_ids=tutorial.id))
            nodes = get_tutorial_specific_nodes(request, self, tutorial.id,
                    self.lecture.id)
            for node in nodes:
                tutorial_root.append(node)
            if tutorial_root.children:
                request.navigationTree.prepend(tutorial_root)

        if lecture_root.children:
            request.navigationTree.prepend(lecture_root)

class AssignStudentContext(object):
    def __init__(self, request):
        student_id = request.POST['student']
        tutorial_id = request.POST['new_tutorial']
        self.student = request.db.query(User).get(student_id)
        self.tutorial = request.db.query(Tutorial).get(tutorial_id)
        if self.student is None:
            raise HTTPNotFound(detail='Student not found')
        if self.tutorial is None:
            raise HTTPNotFound(detail='tutorial not found')
        self.__acl__ = [
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]+[
                        (Allow, 'user:{0}'.format(assistant.id), ('move')) for assistant in self.tutorial.lecture.assistants
                ]


class ExamContext:
    def __init__(self, request):
        exam_id = request.matchdict['exam_id']
        self.exam = request.db.query(Exam).get(exam_id)
        if self.exam is None:
            raise HTTPNotFound(detail='Exam not found')
        self.tutorial_ids_str = request.matchdict.get('tutorial_ids', '')
        self.tutorials, self.tutorial_ids =  getTutorials(request)
        self.__acl__ = [
                #(Allow, Authenticated, 'view_own_points'),
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]+[(Allow, 'user:{0}'.format(tutor.id), ('statistics')) for tutor in self.exam.lecture.tutors
                ]+[(Allow, 'user:{0}'.format(assistant.id), ('edit', 'view_points', 'enter_points', 'statistics')) for assistant in self.exam.lecture.assistants
                ]
        if self.exam.lecture.tutor_rights == editAllTutorials:
            self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('enter_points', 'view_points')) for tutor in self.exam.lecture.tutors]
        else:
            if self.tutorials:
                if self.exam.lecture.tutor_rights == editOwnTutorials:
                    self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('view_points', 'enter_points')) for tutor in getTutorForTutorials(self.tutorials)]
                elif self.exam.lecture.tutor_rights == editNoTutorials:
                    self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('view_points')) for tutor in getTutorForTutorials(self.tutorials)]
                elif self.exam.lecture.tutor_rights == editAllTutorials:
                    self.__acl__ += [(Allow, 'user:{0}'.format(tutor.id), ('view_points', 'enter_points')) for tutor in self.exam.lecture.tutors]
                else: raise ValueError('Tutorrights %s not known' % self.exam.lecture.tutor_rights)

        # add exam specific links
        if self.exam.lecture is None:
            return

        if request.has_permission('edit', self):
            lecture_root = NavigationTree(self.exam.lecture.name,
                    request.route_url('lecture_edit', lecture_id=self.exam.lecture.id))
        else:
            lecture_root = NavigationTree(self.exam.lecture.name,
                    request.route_url('lecture_view', lecture_id=self.exam.lecture.id))
        nodes = get_lecture_specific_nodes(request, self, self.exam.lecture.id)
        for node in nodes:
            lecture_root.append(node)

        request.navigationTree.prepend(lecture_root)

class ExerciseContext:
    def __init__(self, request):
        exercise_id = request.matchdict['exercise_id']
        self.exercise = request.db.query(Exercise).get(exercise_id)
        if self.exercise is None:
            raise HTTPNotFound(detail='Exercise not found')
        self.exam = self.exercise.exam
        if 'tutorial_ids' in request.matchdict:
            self.tutorial_ids = request.matchdict['tutorial_ids'].split(',')
            if len(self.tutorial_ids)==1 and self.tutorial_ids[0]=='':
                self.tutorial_ids = []
                self.tutorials = []
            else:
                self.tutorials = request.db.query(Tutorial).filter(Tutorial.id.in_(self.tutorial_ids)).all()
        self.__acl__ = [
                (Allow, Authenticated, 'view_points'),
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]+[(Allow, 'user:{0}'.format(tutor.id), ('statistics')) for tutor in self.exam.lecture.tutors
                ]+[(Allow, 'user:{0}'.format(assistant.id), ('statistics')) for assistant in self.exam.lecture.assistants
                ]

class CorrelationContext:
    def __init__(self, request):
        source1 = request.GET['source1']
        source2 = request.GET['source2']
        ids1 = self.get_allowed_ids(source1, request)
        ids2 = self.get_allowed_ids(source2, request)
        ids = set(ids1).intersection(set(ids2))
        self.__acl__ = [
                (Allow, 'group:administrators', ALL_PERMISSIONS)
                ] + [(Allow, 'user:{0}'.format(id), ('correlation')) for id in ids]
    def get_allowed_ids(self, source, request):
        source_type, source_id = source.split('_',1)
        if source_type == 'exam':
            exam = request.db.query(Exam).get(source_id)
            if exam:
                return [assistant.id for assistant in exam.lecture.assistants]+[tutor.id for tutor in exam.lecture.tutors]
            else:
                raise HTTPNotFound('Exam not found')
        elif source_type == 'lecture':
            lecture = request.db.query(Lecture).get(source_id)
            if lecture:
                return [assistant.id for assistant in lecture.assistants]+[tutor.id for tutor in lecture.tutors]
            else:
                raise HTTPNotFound('Lecture not found')
        else:
            raise ValueError('Sourcetype not known: %s' % source_type)


class LectureEndpointContext:
    def __init__(self, request):
        lecture_id = request.matchdict.get('lecture_id', None)
        self.__acl__ = [
                (Allow, Authenticated, ('view')),
                (Allow, 'group:administrators', ALL_PERMISSIONS),
                ]+[(Allow, 'user:{0}'.format(a.id), 'create_lecture') for a in request.db.query(User).filter(User.is_assistant==1).all()]

        if lecture_id is not None:
            lecture = request.db.query(Lecture).get(lecture_id)
            if lecture is not None:
                self.__acl__ += [(Allow, 'user:{0}'.format(assistant.id), ('view', 'edit')) for assistant in lecture.assistants]


class TutorialEndpointContext:
    def __init__(self, request):
        tutorial_id = request.matchdict.get('tutorial_id', None)
        self.__acl__ = [(Allow, Authenticated, ('viewOverview')),
                        (Allow, 'group:administrators', ALL_PERMISSIONS)]
        if tutorial_id is not None:
            tutorial = request.db.query(Tutorial).get(tutorial_id)
            if tutorial is not None:
                lecture = tutorial.lecture
                self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('viewAll', 'edit'))] if request.user in lecture.assistants else []
                if lecture.tutor_rights == editOwnTutorials:
                    self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('viewAll'))] if request.user == tutorial.tutor else []
                elif lecture.tutor_rights == editAllTutorials:
                    self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('viewAll'))] if request.user in lecture.tutors else []

class ExamEndpointContext:
    def __init__(self, request):
        exam_id = request.matchdict['exam_id']
        self.exam = request.db.query(Exam).get(exam_id)
        if self.exam is None:
            raise HTTPNotFound(detail='Exam not found')
        lecture = self.exam.lecture
        lecture_students = lecture.students
        self.__acl__ = [(Allow, 'group:administrators', ALL_PERMISSIONS)]
        if request.user in lecture_students:
            self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('view'))]
        self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('view', 'edit'))] if request.user in lecture.assistants else []
        self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('view'))] if request.user in lecture.tutors else []

class ExerciseEndpointContext:
    def __init__(self, request):
        exercise_id = request.matchdict['exercise_id']
        exercise_id = exercise_id.strip("/")
        user_id = request.matchdict.get('user_id', None)
        self.exercise = request.db.query(Exercise).get(exercise_id)
        self.lecture = self.exercise.exam.lecture
        tutorial = None
        self.user = None
        if user_id is not None:
            user_id = user_id.strip("/")
            self.user = request.db.query(User).get(user_id)
            tutorial = request.db.query(LectureStudent).filter(and_(LectureStudent.student_id == self.user.id, LectureStudent.lecture == self.lecture)).one().tutorial
        self.__acl__ = [(Allow, 'group:administrators', ALL_PERMISSIONS)]
        self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('view', 'viewAll', 'viewOwn'))] if request.user in self.lecture.assistants else []
        if request.user == self.user:
            self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('view', 'viewOwn'))]
        if self.lecture.tutor_rights == editAllTutorials:
            self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('view', 'viewAll', 'viewOwn'))] if request.user == self.lecture.tutors else []
        else:
            self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('view'))] if request.user in self.lecture.tutors else []
        if tutorial is not None:
            self.__acl__ += [(Allow, 'user:{0}'.format(request.user.id), ('viewOwn'))] if request.user == tutorial.tutor else []
