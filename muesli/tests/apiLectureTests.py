# -*- coding: utf-8 -*-
#
# muesli/tests/apiTests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2018, Philipp Göldner  <pgoeldner (at) stud.uni-heidelberg.de>
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

ACCEPT_HEADER = {'Accept': 'application/json'}
URL = "/api/v1"


class BaseTests(functionalTests.BaseTests):
    def test_collection_lecture_get(self):
        res = self.testapp.get(URL+'/lectures', ACCEPT_HEADER, status=403)

    def test_lecture_get(self):
        res = self.testapp.get(
            URL+'/lectures/20110', ACCEPT_HEADER, status=403)

    # TODO: add a valid PUT request
    def test_lecture_put(self):
        res = self.testapp.put(URL+'/lectures', {}, ACCEPT_HEADER, status=403)

    def test_lecture_post(self):
        lecture = {
            "term": 20182,
            "name": "Informatik",
            "assistants": [{
                "email": "test@test.de"
            }]
        }
        res = self.testapp.post(URL+'/lectures', lecture, ACCEPT_HEADER, status=403)
