from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc


@resource(collection_path='/api/lectures',
          path='/api/lectures/{id}',
          factory=context.TestContext,
          permission='view')  # TODO Api specific permission
class Lecture(object):
    def __init__(self, request, context=None):  # TODO was ist hier der Kontext
        self.request = request
        self.db = request.db

    def collection_get(self):
        lectures = (
            self.db.query(models.Lecture)
            .order_by(desc(models.Lecture.term), models.Lecture.name)
            .options(joinedload(models.Lecture.assistants))
            .filter(models.Lecture.is_visible == True) # noqa: 712
            .all()
        )
        allowed_attributes_lecture = ['id', 'name', 'lecturer', 'assistants', 'term']
        allowed_attributes_user = ['first_name', 'last_name', 'email']
        self.request.context.setAllowedKeys({'lecture': allowed_attributes_lecture, 'user': allowed_attributes_user})
        return lectures

    def get(self):
        pass
