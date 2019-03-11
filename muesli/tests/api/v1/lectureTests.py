# -*- coding: utf-8 -*-
#
# muesli/tests/api/v1/lectureTests.py
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

import random
import string

from muesli.tests import functionalTests
from muesli.tests.api.v1 import URL, TESTUSERS, STATIC_HEADERS
from muesli.tests.api.v1.utilities import authenticate_testapp

import muesli.models

class BaseTests(functionalTests.BaseTests):
    def test_collection_lecture_get(self):
        self.testapp.get(URL+'/lectures', STATIC_HEADERS, status=403)

    def test_lecture_get(self):
        self.testapp.get(URL+'/lectures/20110', STATIC_HEADERS, status=403)

    def test_lecture_put(self):
        lecture = {"term": 20181, "name": "Irgendwas", "lecturer": "Ich auch"}
        self.testapp.put_json(URL+'/lectures/20109', lecture, headers=STATIC_HEADERS, status=403)

    def test_lecture_post(self):
        lecture = {
            "term": 20182,
            "name": "Informatik",
            "assistants": [{
                "email": "assistant@muesli.org"
            }]
        }
        self.testapp.post(URL+'/lectures', lecture, STATIC_HEADERS, status=403)


class AssistantLoggedInTests(functionalTests.PopulatedTests):
    def setUp(self):
        functionalTests.PopulatedTests.setUp(self)
        self.api_tokens = {
            user[0]: authenticate_testapp(
                self.testapp, user[0], user[1]
            ) for user in TESTUSERS
        }

    def test_collection_lecture_get(self):
        self.testapp.get(URL+'/lectures', headers=self.api_tokens["assistant@muesli.org"], status=200)

    def test_lecture_get(self):
        lecture_id = self.testapp.get(URL+'/lectures', headers=self.api_tokens["assistant@muesli.org"]).json_body[0]["id"]
        self.testapp.get(URL+'/lectures/'+str(lecture_id), headers=self.api_tokens["assistant@muesli.org"], status=200)

    def test_lecture_post(self):
        pre_count = self.session.query(muesli.models.Lecture).count()
        lecture = {"term": 20182, "name": "Informatik", "assistants": [{"email": "assistant@muesli.org"}]}
        res = self.testapp.post_json(URL+'/lectures', lecture, headers=self.api_tokens["assistant@muesli.org"])
        self.assertTrue((pre_count+1) == self.session.query(muesli.models.Lecture).count())
        created_lecture = self.session.query(muesli.models.Lecture).get(res.json["created"]["id"])
        self.assertTrue(created_lecture is not None)

    def test_lecture_put(self):
        lecture = self.session.query(muesli.models.Lecture).first()
        lecture_id = lecture.id
        teststring = ''.join(random.choice(string.ascii_uppercase) for _ in range(10))
        put_data = {"term": 20181, "name": teststring, "lecturer": "Ich auch"}
        self.testapp.put_json(URL+'/lectures/'+str(lecture_id), put_data, headers=self.api_tokens["assistant@muesli.org"], status=200)
        self.session.refresh(lecture)
        lecture = self.session.query(muesli.models.Lecture).get(lecture_id)
        self.assertTrue(lecture.name == teststring)

class AdminLoggedInTests(functionalTests.PopulatedTests):
    def setUp(self):
        functionalTests.PopulatedTests.setUp(self)
        self.api_tokens = {
            user[0]: authenticate_testapp(
                self.testapp, user[0], user[1]
            ) for user in TESTUSERS
        }

    def test_collection_lecture_get(self):
        self.testapp.get(URL+'/lectures', headers=self.api_tokens["admin@muesli.org"], status=200)

    def test_lecture_get(self):
        lecture_id = self.testapp.get(URL+'/lectures', headers=self.api_tokens["admin@muesli.org"]).json_body[0]["id"]
        self.testapp.get(URL+'/lectures/'+str(lecture_id), headers=self.api_tokens["admin@muesli.org"], status=200)

    def test_lecture_post(self):
        pre_count = self.session.query(muesli.models.Lecture).count()
        lecture = {"term": 20182, "name": "Informatik", "assistants": [{"email": "assistant@muesli.org"}]}
        res = self.testapp.post_json(URL+'/lectures', lecture, headers=self.api_tokens["admin@muesli.org"])
        self.assertTrue((pre_count+1) == self.session.query(muesli.models.Lecture).count())
        created_lecture = self.session.query(muesli.models.Lecture).get(res.json["created"]["id"])
        self.assertTrue(created_lecture is not None)

    def test_lecture_put(self):
        lecture = self.session.query(muesli.models.Lecture).first()
        lecture_id = lecture.id
        teststring = ''.join(random.choice(string.ascii_uppercase) for _ in range(10))
        put_data = {"term": 20181, "name": teststring, "lecturer": "Ich auch"}
        self.testapp.put_json(URL+'/lectures/'+str(lecture_id), put_data, headers=self.api_tokens["admin@muesli.org"], status=200)
        self.session.refresh(lecture)
        lecture = self.session.query(muesli.models.Lecture).get(lecture_id)
        self.assertTrue(lecture.name == teststring)
