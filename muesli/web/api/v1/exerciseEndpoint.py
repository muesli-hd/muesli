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

from cornice.resource import resource, view
from sqlalchemy import and_

from muesli import models
from muesli.web import context


@resource(collection_path=r'/exercises/{exercise_id:(\d+)+\/?}',
          path=r'/exercises/{exercise_id:\d+}/{user_id:(\d+)+\/?}',
          factory=context.ExerciseEndpointContext,
          permission='view')
class Exercise:
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def collection_get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
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
        exercise = self.request.context.exercise
        exer_schema = models.ExerciseSchema()
        exer_student_schema = models.ExerciseStudentSchema(many=True, exclude=["points"])
        tutorials = [tut for tut in self.request.context.lecture.tutorials if tut.tutor == self.request.user]  # It is possible to be tutor of more than 1 tutorial
        if self.request.has_permission('viewAll'):
            exer_students = self.request.db.query(models.ExerciseStudent).filter(models.ExerciseStudent.exercise == exercise).all()
            result = exer_schema.dump(exercise)
            result.update({"exercise_students": exer_student_schema.dump(exer_students)})
        elif tutorials:
            exer_students = []
            for tutorial in tutorials:
                exer_students += self.request.db.query(models.ExerciseStudent).join(models.ExerciseStudent.student).filter(and_(models.ExerciseStudent.exercise == exercise,
                                                                                                                                models.User.id.in_([stud.id for stud in tutorial.students]))).all()
            result = exer_schema.dump(exercise)
            result.update({"exercise_students": exer_student_schema.dump(exer_students)})

        return result

    @view(permission='viewOwn')
    def get(self):
        """
        ---
        get:
          security:
            - Bearer: [read]
            - Basic: [read]
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
        exercise = self.request.context.exercise
        user = self.request.context.user
        exer_students = exercise.exam.exercise_points.filter(models.ExerciseStudent.student_id == user.id)
        exer_student_schema = models.ExerciseStudentSchema(many=True)
        result = exer_student_schema.dump(exer_students)
        return result
