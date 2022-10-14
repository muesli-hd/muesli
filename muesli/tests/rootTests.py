# -*- coding: utf-8 -*-
#
# muesli/tests/rootTests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2011, Matthias Kuemmerer <matthias (at) matthias-k.org>
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
import muesli.web
from muesli.tests import functionalTests

class BaseTests(functionalTests.BaseTests):
    def test_index(self):
        # Logged out users are redirected to the login page
        res = self.testapp.get('/', status=302)

    def test_overview(self):
        res = self.testapp.get('/overview', status=302)

    def test_admin(self):
        res = self.testapp.get('/admin', status=403)

    def test_contact(self):
        res = self.testapp.get('/contact', status=200)

    def test_email_users(self):
        res = self.testapp.get('/email_users', status=403)

    def test_favicon(self):
        res = self.testapp.get('/favicon.ico', status=200)

class UnloggedTests(BaseTests,functionalTests.PopulatedTests):
    pass

class UserLoggedInTests(UnloggedTests):
    def setUp(self):
        UnloggedTests.setUp(self)
        self.setUser(self.user)

    def test_overview(self):
        # Now we are logged in, thus we should
        # get 200 instead of 302
        res = self.testapp.get('/overview', status=200)

    def test_overview_full(self):
        # Now we are logged in, thus we should
        # get 200 instead of 302
        res = self.testapp.get('/overview?show_all=1', status=200)

class TutorLoggedInTests(UserLoggedInTests):
    def setUp(self):
        UserLoggedInTests.setUp(self)
        self.setUser(self.tutor)

class AssistantLoggedInTests(TutorLoggedInTests):
    def setUp(self):
        TutorLoggedInTests.setUp(self)
        self.setUser(self.assistant)


class AdminLoggedInTests(AssistantLoggedInTests):
    def setUp(self):
        AssistantLoggedInTests.setUp(self)
        self.setUser(self.admin)

    def test_admin(self):
        res = self.testapp.get('/admin', status=200)

    def test_email_users(self):
        res = self.testapp.get('/email_users', status=200)
        res = self.testapp.get('/email_users?type=unconfirmed', status=200)
