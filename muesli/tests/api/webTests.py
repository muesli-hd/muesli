# -*- coding: utf-8 -*-
#
# muesli/tests/api/webTests.py
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
from muesli.models import BearerToken


class BaseTests(functionalTests.BaseTests):
    def test_api_keys(self):
        self.testapp.get('/user/api_keys', status=403)

    def test_api_explorer(self):
        self.testapp.get('/api-explorer', status=200)

class UserLoggedInTests(functionalTests.PopulatedTests):
    def setUp(self):
        functionalTests.PopulatedTests.setUp(self)
        self.setUser(self.user)

    def test_api_keys(self):
        self.testapp.get('/user/api_keys', status=200)

    def test_api_explorer(self):
        self.testapp.get('/api-explorer', status=200)

    def test_key_generation(self):
        res = self.testapp.get('/user/api_keys', status=200)
        tokens = self.session.query(BearerToken).filter_by(user_id=self.user.id).filter(BearerToken.revoked == False)
        tokens_pre = len(tokens.all())
        teststring = ''.join(random.choice(string.ascii_uppercase) for _ in range(10))
        form = res.form
        form["description"] = teststring
        res_post_submit = form.submit("submit")
        search_str = '/user/remove_api_key/'
        start = res_post_submit.text.find(search_str)
        start += len(search_str)
        # Assumes token_id's < 1000
        token_id = int(res_post_submit.text[start: start+3])
        self.assertTrue(res.status.startswith('200'))
        created_token = self.session.query(BearerToken).filter_by(user_id=self.user.id).filter(BearerToken.revoked == False).first()
        tokens_post = len(tokens.all())
        self.assertResContains(res_post_submit, teststring)
        self.assertTrue(created_token.description == teststring)
        self.assertTrue(created_token.id == token_id)
        self.assertTrue((tokens_pre+1) == tokens_post)
