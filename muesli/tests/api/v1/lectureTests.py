# -*- coding: utf-8 -*-
#
# muesli/tests/apiTests.py
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

from muesli.tests import functionalTests

from muesli.tests.api.v1 import URL, API_TOKENS, TESTUSERS, STATIC_HEADERS

class BaseTests(functionalTests.BaseTests):
    def test_collection_lecture_get(self):
        res = self.testapp.get(URL+'/lectures', STATIC_HEADERS, status=403)

    def test_lecture_get(self):
        res = self.testapp.get(
            URL+'/lectures/20110', STATIC_HEADERS, status=403)

    def test_lecture_put(self):
        lecture = '{"term": 20181, "name": "Irgendwas", "lecturer": "Ich auch"}'
        res = self.testapp.put(URL+'/lectures/20109', lecture, STATIC_HEADERS, status=403)

    def test_lecture_post(self):
        lecture = {
            "term": 20182,
            "name": "Informatik",
            "assistants": [{
                "email": "test@test.de"
            }]
        }
        res = self.testapp.post(URL+'/lectures', lecture, STATIC_HEADERS, status=403)


class UnloggedTests(functionalTests.PopulatedTests):
    def authenticate(self, username, password) -> dict:
        """A function to authenticate as a user and get the valid headers for this
        user.

        Args:
            username: A string with the username to authenticate as.
            password: The password for the respective user.
        Returns:
            A dictionary with the needed headers for authorization towards the v1
            Muesli API.

            example: (<TOKEN> is the corresponding JWT token)
                {
                    'Authorization': 'Bearer <TOKEN>',
                    'Accept': 'application/json'
                }

        """

        r = self.testapp.post(
            URL+'/login',
            {"email": username, "password": password},
            STATIC_HEADERS,
        )
        token = r.json.get("token", "")
        header_content = {'Authorization': 'Bearer '+token}
        header_content.update(STATIC_HEADERS)
        return header_content

    # def setUp(self):
        # from muesli.models import User
        # from muesli.tests.functionalTests import setUserPassword
        # self.user2 = User()
        # self.user2.first_name = 'Sigmund'
        # self.user2.last_name = 'Student'
        # self.user2.email = 'user2@muesli.org'
        # self.user2.subject = "Mathematik (BSc)"
        # setUserPassword(self.user2, 'user2password')
        # self.session.add(self.user2)
        # self.setUser(self.user2)

    def test_lecture_post(self):
        self.API_TOKENS = {user[0]: self.authenticate(user[0], user[1]) for user in TESTUSERS}
        lecture = {
            "term": 20182,
            "name": "Informatik",
            "assistants": [{
                "email": "test@test.de"
            }]
        }
        res = self.testapp.post(URL+'/lectures', lecture, STATIC_HEADERS, status=403)

