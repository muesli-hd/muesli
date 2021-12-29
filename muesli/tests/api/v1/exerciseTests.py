# -*- coding: utf-8 -*-
#
# muesli/tests/api/v1/exerciseTests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2019, Philipp Göldner  <goeldner (at) stud.uni-heidelberg.de>
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

from muesli.tests import functionalTests
from muesli.tests.api.v1 import URL, TESTUSERS, STATIC_HEADERS
from muesli.tests.api.v1.utilities import authenticate_testapp
from muesli.models import ExerciseStudent


class BaseTests(functionalTests.BaseTests):
    def test_collection_exercise_get(self):
        self.testapp.get(URL+'/exercises/6723', headers=STATIC_HEADERS, status=404)

    def test_exercise_get(self):
        self.testapp.get(URL+'/exercises/6723/67209', headers=STATIC_HEADERS, status=404)

class StudentLoggedInTests(functionalTests.PopulatedTests):
    def setUp(self):
        functionalTests.PopulatedTests.setUp(self)
        self.api_token = authenticate_testapp(self.testapp, TESTUSERS["tutor@muesli.org"])

        # TODO: Integrate this into functionalTests.PopulatedTests.populate()
        self.exerciseStudent = ExerciseStudent()
        self.exerciseStudent.exercise = self.exercise
        self.exerciseStudent.points = 1
        self.exerciseStudent.student = self.user
        self.exerciseStudent.student_id = self.user.id

    def test_collection_exercise_get(self):
        self.testapp.get(
            URL+'/exercises/'+str(self.exercise.id),
            headers=self.api_token,
            status=200
        )

    def test_exercise_get(self):
        self.testapp.get(
            URL+'/exercises/{}/{}/'.format(
                self.exerciseStudent.exercise.id,
                self.exerciseStudent.student.id
            ),
            headers=self.api_token,
            status=200
        )
