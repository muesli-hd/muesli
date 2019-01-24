
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


class BaseTests(functionalTests.BaseTests):
    def test_apispec(self):
        res = self.testapp.get('/openapi.json', status=200)

    def test_collection_lecture(self):
        res = self.testapp.get('/api/lectures', status=403)

    def test_lecture(self):
        res = self.testapp.get('/api/lectures/20110', status=403)

    def test_tutorials_collection(self):
        res = self.testapp.get('/api/tutorials', status=403)

    def test_tutorials(self):
        res = self.testapp.get('/api/tutorials/46839', status=403)
