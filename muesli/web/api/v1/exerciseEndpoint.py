# -*- coding: utf-8 -*-
#
# muesli/web/api/v1/exerciseEndpoint.py
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

from cornice.resource import resource

from muesli import models
from muesli.web import context


@resource(collection_path='/exercises/{exercise_id:(\d+)+\/?}',
          path='/exercises/{exercise_id:\d+}/{user_id:(\d+)+\/?}',
          factory=context.GeneralContext,
          permission='view')  # TODO Api specific permission
class Exercise(object):
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
          tags:
            - "v1"
          summary: "return an exercise for given student"
          description: ""
          operationId: "exercise_student_get"
          produces:
            - "application/json"
          responses:
            200:
              description: successfull return of the exercise
              schema:
                $ref: "#/definitions/ExerciseStudent"
        """
        exercise_id = self.request.matchdict["exercise_id"]
        user_id = self.request.matchdict["user_id"]
        # get rid of the trailing slash
        user_id = user_id.strip("/")
        exercise = self.request.db.query(models.Exercise).get(exercise_id)
        user = self.request.db.query(models.User).get(user_id)
        exer_students = exercise.exam.exercise_points.filter(models.ExerciseStudent.student_id == user.id)
        exer_student_schema = models.ExerciseStudentSchema(many=True)
        result = exer_student_schema.dump(exer_students)
        return result

    def collection_get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
          tags:
            - "v1"
          summary: "return an exercise"
          description: ""
          operationId: "exercise_get"
          produces:
            - "application/json"
          responses:
            200:
              description: successfull return of the exercises
              schema:
                $ref: "#/definitions/Exercise"
        """
        exercise_id = self.request.matchdict["exercise_id"]
        # get rid of the trailing slash
        exercise_id = exercise_id.strip("/")
        exercise = self.request.db.query(models.Exercise).get(exercise_id)
        exer_schema = models.ExerciseSchema()
        exer_student_schema = models.ExerciseStudentSchema(many=True, exclude=["points"])
        exer_students = self.request.db.query(models.ExerciseStudent).filter(models.ExerciseStudent.exercise_id == exercise_id).all()
        result = exer_schema.dump(exercise)
        result.update({"exercise_students": exer_student_schema.dump(exer_students)})
        return result
