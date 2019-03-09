# -*- coding: utf-8 -*-
#
# muesli/web/api/v1/lectureEndpoint.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2018, Philipp Göldner  <goeldner (at) stud.uni-heidelberg.de>
#                     Christian Heusel <christian (at) heusel.eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from cornice.resource import resource, view
from muesli import models
from muesli.web import context
from muesli.web.api.v1 import allowed_attributes

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc
from marshmallow.exceptions import ValidationError


@resource(collection_path='/lectures',
          path='/lectures/{lecture_id}',
          factory=context.LectureEndpointContext)
class Lecture:
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    @view(permission='view')
    def collection_get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
          tags:
            - "v1"
          summary: "return all lectures"
          description: ""
          operationId: "lecture_get"
          consumes:
            - "application/json"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/CollectionLecture"
        """
        lectures = (
            self.db.query(models.Lecture)
            .order_by(desc(models.Lecture.term), models.Lecture.name)
            .options(joinedload(models.Lecture.assistants))
            .filter(models.Lecture.is_visible == True)
            .all()
        )
        schema = models.LectureSchema(many=True, only=allowed_attributes.collection_lecture())
        return schema.dump(lectures)

    @view(permission='view')
    def get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
          tags:
            - "v1"
          summary: "return a specific lecture"
          description: ""
          operationId: "lecture_collection_get"
          produces:
            - "application/json"
          responses:
            200:
              description: successfull return of the lecture
              schema:
                $ref: "#/definitions/Lecture"
        """
        lecture_id = self.request.matchdict['lecture_id']
        lecture = self.db.query(models.Lecture).options(undefer('tutorials.student_count'), joinedload(models.Lecture.assistants), joinedload(models.Lecture.tutorials)).get(lecture_id)
        subscribed = self.request.user.id in [s.id for s in lecture.students]
        allowed_attr = allowed_attributes.lecture()
        if lecture.mode == 'off':
            allowed_attr = allowed_attributes.lecture()
            allowed_attr.remove('tutorials')
        schema = models.LectureSchema(only=allowed_attr)
        response = schema.dump(lecture)
        if lecture.mode == 'off':
            response.update({'tutorials': []})
        return {'lecture': response,
                'subscribed': subscribed}

    @view(permission='edit')
    def put(self):
        """
        ---
        put:
          security:
            - Bearer: [write]
          tags:
            - "v1"
          summary: "update a lecture object"
          description: "test123"
          operationId: "lecture_put"
          produces:
            - "application/json"
          consumes:
            - "application/json"
          parameters:
          - in: "body"
            name: "body"
            description: ""
            required: true
            schema:
              $ref: "#/definitions/Lecture"
          responses:
            200:
              description: successfull update of a lecture
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: ok
                  updated:
                    $ref: "#/definitions/CollectionLecture"
            400:
              description: HTTPBadRequest (Example uses A bad attribute)
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: error
                  error:
                    type: array
                    example: [{'description': {'name': ['Missing data for required field.'], 'test123': ['Unknown field.']}, 'name': 'fail', 'location': 'body'}]
        """
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
        """
        ---
        post:
          security:
            - Bearer: [write]
          tags:
            - "v1"
          summary: "create a lecture"
          description: "test123"
          operationId: "lecture_collection_post"
          produces:
            - "application/json"
          consumes:
            - "application/json"
          parameters:
          - in: "body"
            name: "body"
            description: ""
            required: true
            schema:
              $ref: "#/definitions/Lecture"
          responses:
            200:
              description: successfull creation of a lecture
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: ok
                  created:
                    $ref: "#/definitions/CollectionLecture"
            400:
              description: HTTPBadRequest (Example uses A bad attribute)
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: error
                  error:
                    type: array
                    example: [{'description': {'name': ['Missing data for required field.'], 'test123': ['Unknown field.']}, 'name': 'fail', 'location': 'body'}]
        """
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
