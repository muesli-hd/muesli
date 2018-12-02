from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc
#import json


@resource(collection_path='/api/lectures',
          path='/api/lectures/{id}',
          factory=context.LectureContext,
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
            .filter(models.Lecture.is_visible == True) # noqa: 712
            .all()
        )
        allowed_attributes_lecture = ['id', 'name', 'lecturer', 'assistants','term']
        allowed_attributes_user = ['first_name', 'last_name', 'email']
        #lecture_dicts = [lecture.__dict__ for lecture in lectures]
        # Implement something like this in #61
        #for lecture in lecture_dicts:
        #    for key in list(lecture.keys()):  # Iterating over list of lecture keys bc. iterating over lecture and changing it doesn't work
        #        if key not in allowed_attributes_lecture:
        #            lecture.pop(key)

        #for lecture in lecture_dicts:
        #    lecture['assistants'] = [assistant.__dict__ for assistant in lecture['assistants']]
        #    for assistant in lecture['assistants']:
        #        for key in list(assistant.keys()):
        #            if key not in allowed_attributes_user:
        #                assistant.pop(key)
        return lectures  # TODO call remove dict function see #61 on github

    def get(self):
        # TODO return useful stuff
        return {"test": "test"}
