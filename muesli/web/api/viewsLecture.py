from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc


@resource(collection_path='/api/lectures',
          path='/api/lectures/{lecture_id}',
          factory=context.GeneralContext,
          permission='view')  # TODO Api specific permission
class Lecture(object):
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def collection_get(self):
        lectures = (
            self.db.query(models.Lecture)
            .order_by(desc(models.Lecture.term), models.Lecture.name)
            .options(joinedload(models.Lecture.assistants))
            .filter(models.Lecture.is_visible == True) # noqa
            .all()
        )
        allowed_attr_lecture = ['id', 'name', 'lecturer', 'assistants', 'term']
        schema = models.LectureSchema(many=True, only=allowed_attr_lecture)
        return schema.dump(lectures)

    def get(self):
        lecture_id = self.request.matchdict['lecture_id']
        lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count'), joinedload(models.Lecture.assistants), joinedload(models.Lecture.tutorials)).get(lecture_id)
        # TODO What are these?
        times = lecture.prepareTimePreferences(user=self.request.user)
        subscribed = self.request.user.id in [s.id for s in lecture.students]
        allowed_attr_lecture = [
            'id',
            'name',
            'lecturer',
            'assistants',
            'term',
            'url',
            'tutorials',
        ]

        schema = models.LectureSchema(only=allowed_attr_lecture)
        return {'lecture': schema.dump(lecture),
                'subscribed': subscribed,
                'times': times}

