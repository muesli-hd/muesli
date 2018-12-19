from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc


@resource(collection_path='/api/tutorials',
          path='/api/tutorials/{tutorial_id}',
          factory=context.GeneralContext,
          permission='view')  # TODO Api specific permission
class Tutorial(object):
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def collection_get(self):
        tutorials = self.request.user.tutorials.options(joinedload(models.Tutorial.tutor), joinedload(models.Tutorial.lecture))
        #allowed_attr_tutorials = ['id', 'name', 'lecturer', 'assistants', 'term']
        # TODO Look at LectureStudent ExamStudent and Exam
        schema = models.TutorialSchema(many=True)#, only=allowed_attr_lecture)
        return schema.dump(tutorials)

    def get(self):
        pass
        #lecture_id = self.request.matchdict['lecture_id']
        #lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count'), joinedload(models.Lecture.assistants), joinedload(models.Lecture.tutorials)).get(lecture_id)
        ## TODO What are these?
        #times = lecture.prepareTimePreferences(user=self.request.user)
        #subscribed = self.request.user.id in [s.id for s in lecture.students]
        #allowed_attr_lecture = [
        #    'id',
        #    'name',
        #    'lecturer',
        #    'assistants',
        #    'term',
        #    'url',
        #    'tutorials',
        #]

        #schema = models.LectureSchema(only=allowed_attr_lecture)
        #return {'lecture': schema.dump(lecture),
        #        'subscribed': subscribed,
        #        'times': times}

