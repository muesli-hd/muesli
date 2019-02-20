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

from muesli.tests.api import v1

class BaseTests(functionalTests.BaseTests):
    def test_collection_lecture_get(self):
        res = self.testapp.get(v1.URL+'/lectures', v1.ACCEPT_HEADER, status=403)

    def test_lecture_get(self):
        res = self.testapp.get(
            v1.URL+'/lectures/20110', v1.ACCEPT_HEADER, status=403)

    def test_lecture_put(self):
        lecture = '{"term": 20181, "name": "Irgendwas", "lecturer": "Ich auch"}'
        res = self.testapp.put(v1.URL+'/lectures/20109', lecture, v1.ACCEPT_HEADER, status=403)

    def test_lecture_post(self):
        lecture = {
            "term": 20182,
            "name": "Informatik",
            "assistants": [{
                "email": "test@test.de"
            }]
        }
        res = self.testapp.post(v1.URL+'/lectures', lecture, v1.ACCEPT_HEADER, status=403)
