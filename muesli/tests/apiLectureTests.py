
# -*- coding: utf-8 -*-
#
# muesli/tests/apiTests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2019, Christian Heusel <christian (at) heusel.eu>
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

import unittest
from muesli.tests import functionalTests

accept_header = {'Accept': 'application/json'}

class BaseTests(functionalTests.BaseTests):
    def test_collection_lecture_get(self):
        res = self.testapp.get('/api/lectures', accept_header, status=403)

    def test_lecture_get(self):
        res = self.testapp.get('/api/lectures/20110', accept_header, status=403)

    # TODO: add a valid PUT request
    def test_lecture_put(self):
        res = self.testapp.put('/api/lectures', {}, accept_header, status=403)

    def test_lecture_post(self):
        lecture = {"term": 20182, "name": "Informatik", "assistants": [{"email": "test@test.de"}]}
        res = self.testapp.post('/api/lectures', lecture, accept_header, status=403)

