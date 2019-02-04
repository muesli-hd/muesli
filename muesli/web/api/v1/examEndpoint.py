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

from cornice.resource import resource

from muesli import models
from muesli.web import context

from sqlalchemy.orm import exc, joinedload, undefer
from sqlalchemy.sql.expression import desc
from pyramid.httpexceptions import HTTPBadRequest


@resource(path='/exams/{exam_id}',
          factory=context.GeneralContext,
          permission='view')  # TODO Api specific permission
class Exam(object):
    def __init__(self, request, context=None):
        self.request = request
        self.db = request.db

    def get(self):  # TODO Check if Lecture Student maybe list all lecturestudents
        exam_id = self.request.matchdict["exam_id"]
        exam = self.request.db.query(models.Exam).get(exam_id)
        if exam is None:
            raise HTTPBadRequest("The exam you want to access does not exist!")
        exer_schema = models.ExerciseSchema(many=True)
        exam_schema = models.ExamSchema()
        result = exam_schema.dump(exam)
        result.update({"exercises": exer_schema.dump(exam.exercises)})
        return result


