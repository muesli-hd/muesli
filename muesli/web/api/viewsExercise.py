from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc


@resource(collection_path='/api/exercises',
          path='/api/exercise/{exercise_id}',
          factory=context.GeneralContext,
          permission='view')  # TODO Api specific permission
class Exercise(object):
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def collection_get(self):
        pass

    def get(self):
        pass
