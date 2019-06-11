# -*- coding: utf-8 -*-
#
# muesli/web/api/v1/tutorialEndpoint.py
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

from marshmallow.exceptions import ValidationError
from cornice.resource import resource, view
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from pyramid.httpexceptions import HTTPBadRequest

from muesli import models
from muesli.web import context
from muesli.web.api.v1 import allowed_attributes


@resource(collection_path='/tutorials',
          path='/tutorials/{tutorial_id}',
          factory=context.TutorialEndpointContext,)
class Tutorial:
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    @view(permission='viewOverview')
    def collection_get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
          tags:
            - "v1"
          summary: "return all tutorials"
          description: ""
          operationId: "tutorial_collection_get"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/CollectionTutorial"
        """
        tutorials = self.request.user.tutorials.options(joinedload(models.Tutorial.tutor), joinedload(models.Tutorial.lecture)).all()
        tutorials_as_tutor = self.request.user.tutorials_as_tutor.options(joinedload(models.Tutorial.tutor), joinedload(models.Tutorial.lecture)).all()
        schema = models.TutorialSchema(many=True, only=allowed_attributes.collection_tutorial())
        return schema.dump(tutorials+tutorials_as_tutor)

    @view(permission='viewOverview')
    def get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
          tags:
            - "v1"
          summary: "return a specific tutorial"
          description: ""
          operationId: "tutorial_get"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/Tutorial"
        """
        try:
            tutorial = self.request.db.query(models.Tutorial).options(
                joinedload(models.Tutorial.tutor),
                joinedload(models.Tutorial.lecture)).filter(
                    models.Tutorial.id == self.request.matchdict['tutorial_id'] # pylint: disable=C0121
                ).one()
        except NoResultFound:
            raise HTTPBadRequest("Ungueltige Tutorial ID!")
        exa = tutorial.lecture.exams.filter((models.Exam.results_hidden == False)|(models.Exam.results_hidden == None)) # pylint: disable=C0121
        if self.request.has_permission('viewAll'):
            tut_schema = models.TutorialSchema()
        else:
            tut_schema = models.TutorialSchema(only=allowed_attributes.tutorial())
        exam_schema = models.ExamSchema(many=True, only=["id", "name"])

        result = tut_schema.dump(tutorial)
        try:
            lecture_student = tutorial.lecture.lecture_students.filter(models.LectureStudent.student_id == self.request.user.id).one()
        except NoResultFound:
            lecture_student = None
        # If the user is part of the tutorial he is allowed to view the exams
        if self.request.has_permission('viewAll') or lecture_student:
            result.update({"exams": exam_schema.dump(exa)})
        return result

    @view(permission='edit')
    def collection_post(self):
        """
        ---
        post:
          security:
            - Bearer: [write]
            - Basic: [write]
          tags:
            - "v1"
          summary: "create a tutorial"
          operationId: "tutorial_collection_post"
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
              $ref: "#/definitions/Tutorial"
          responses:
            200:
              description: successfull creation of a tutorial
              schema:
                type: object
                properties:
                  result:
                    type: string
                    example: ok
                  created:
                    $ref: "#/definitions/CollectionTutorial"
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
        schema = models.TutorialSchema()
        schema.context['session'] = self.request.db
        try:
            result = schema.load(self.request.json_body)
        except ValidationError as e:
            self.request.errors.add('body', 'fail', e.messages)
        else:
            tutorial = models.Tutorial(**result)
            self.db.add(tutorial)
            self.db.commit()
            return {'result': 'ok', 'created': schema.dump(tutorial)}
