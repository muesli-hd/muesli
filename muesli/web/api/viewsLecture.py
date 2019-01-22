from cornice.resource import resource, view
from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc
from marshmallow.exceptions import ValidationError
from pyramid.view import view_config


@resource(collection_path='/api/lectures',
          path='/api/lectures/{lecture_id}',
          factory=context.LectureEndpointContext)
class Lecture(object):
    """A greeting endpoint.

    ---
    x-extension: value
    get:
        description: some description
        responses:
            200:
                description: response for 200 code
                schema:
                    $ref: #/definitions/LectureSchema
    """
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    #TODO view_config vs view
    @view_config(context=context.LectureEndpointContext, permission='view')
    def collection_get(self):
        """A greeting endpoint.

        ---
        x-extension: value
        get:
            description: some description
            responses:
                200:
                    description: response for 200 code
                    schema:
                        $ref: #/definitions/BarBodySchema
        """
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

    @view(permission='view')
    def get(self):
        """A greeting endpoint.

        ---
        x-extension: value
        get:
            description: some description
            responses:
                200:
                    description: response for 200 code
                    schema:
                        $ref: #/definitions/BarBodySchema
        """
        lecture_id = self.request.matchdict['lecture_id']
        lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count'), joinedload(models.Lecture.assistants), joinedload(models.Lecture.tutorials)).get(lecture_id)
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

    @view(permission='edit')
    def put(self):
        lecture_id = self.request.matchdict['lecture_id']
        lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count'), joinedload(models.Lecture.assistants)).get(lecture_id)
        schema = models.LectureSchema()
        # attatch db session to schema so it can be used during validation
        schema.context['session'] = self.request.db
        try:
            result = schema.load(self.request.json_body, partial=True)
        except ValidationError as e:
            self.request.errors.add('body', 'fail', e.messages)
        else:
            for k, v in result.items():
                setattr(lecture, k, v)
                # TODO do we need to catch this exception?
            try:
                self.db.commit()
            except exc.SQLAlchemyError:
                # TODO better exception
                self.db.rollback()
            else:
                return {'result': 'ok', 'update': self.get()}

    @view(permission='create_lecture')
    def collection_post(self):
        schema = models.LectureSchema()
        schema.context['session'] = self.request.db
        try:
            result = schema.load(self.request.json_body)
        except ValidationError as e:
            self.request.errors.add('body', 'fail', e.messages)
        else:
            lecture = models.Lecture(**result)
            self.db.add(lecture)
            self.db.commit()
            return {'result': 'ok', 'created': schema.dump(lecture)}
