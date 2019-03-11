# -*- coding: utf-8 -*-
#
# muesli/tests/api/v1/tutorialTests.py
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

import random
import string

from muesli.tests import functionalTests
from muesli.tests.api.v1 import URL, TESTUSERS, STATIC_HEADERS
from muesli.tests.api.v1.utilities import authenticate_testapp

import muesli.models

class BaseTests(functionalTests.BaseTests):
    def test_collection_tutorial_get(self):
        self.testapp.get(URL+'/tutorials', headers=STATIC_HEADERS, status=403)

    def test_tutorial_get(self):
        self.testapp.get(URL+'/tutorials/46838', headers=STATIC_HEADERS, status=403)

    def test_tutorial_post(self):
        tutorial = {
            "lecture_id": "20109",
            "place": "Mathematikon",
            "time": "0 12:00",
            "max_students": "5",
        }
        self.testapp.post(URL+'/tutorials', tutorial, headers=STATIC_HEADERS, status=403)


class StudentLoggedInTests(functionalTests.PopulatedTests):
    def setUp(self):
        functionalTests.PopulatedTests.setUp(self)
        self.api_tokens = {
            user[0]: authenticate_testapp(
                    self.testapp, user[0], user[1]
                )
            for user in TESTUSERS
        }
        self.api_token = authenticate_testapp(self.testapp, "user@muesli.org", "userpassword")

    def test_collection_tutorials_get(self):
        self.testapp.get(URL+'/tutorials', headers=self.api_token, status=200)

    def test_tutorial_get(self):
        tutorial_id = self.testapp.get(URL+'/tutorials', headers=self.api_token).json_body[0]["id"]
        self.testapp.get(URL+'/tutorials/'+str(tutorial_id), headers=self.api_token, status=200)

    def test_tutorial_post(self):
        tutorial = {
            "lecture_id": "20109",
            "place": "Mathematikon",
            "time": "0 12:00",
            "max_students": "5",
        }
        self.testapp.post(URL+'/tutorials', tutorial, headers=self.api_token, status=403)
