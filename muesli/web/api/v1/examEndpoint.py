# -*- coding: utf-8 -*-
#
# muesli/web/api/v1/examEndpoint.py
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


@resource(path='/exams/{exam_id}',
          factory=context.ExamEndpointContext,
          permission='view')
class Exam:
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    @view(permission='view')
    def get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
          tags:
            - "v1"
          summary: "return all lectures"
          description: ""
          operationId: "exam_get"
          consumes:
            - "application/json"
          produces:
            - "application/json"
          responses:
            200:
              description: "response for 200 code"
              schema:
                $ref: "#/definitions/Exam"
        """
        exam = self.request.context.exam
        exer_schema = models.ExerciseSchema(many=True)
        exam_schema = models.ExamSchema()
        result = exam_schema.dump(exam)
        result.update({"exercises": exer_schema.dump(exam.exercises)})
        return result
