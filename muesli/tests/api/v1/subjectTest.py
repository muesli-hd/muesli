# -*- coding: utf-8 -*-
#
# muesli/tests/api/v1/tutorialTests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2022, Tobias Wackenhut <tobias (at) wackenhut.at>
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

import json

from muesli.tests import functionalTests
from muesli.tests.api.v1 import URL, TESTUSERS, STATIC_HEADERS
from muesli.tests.api.v1.utilities import authenticate_testapp


class BaseTests(functionalTests.PopulatedTests):
    headers = STATIC_HEADERS
    expected_status = {
        'get_collection': 403,
        'get': 403,
        'put': 403,
        'post': 403,
        'delete': 403,
    }

    def test_collection_subject_get(self):
        self.testapp.get(f"{URL}/subjects", headers=self.headers, status=self.expected_status['get_collection'])

    def test_subject_get(self):
        self.testapp.get(f"{URL}/subjects/{self.non_curated_subject.id}", headers=self.headers, status=self.expected_status['get'])

    def test_subject_put(self):
        subject = {
            "name": "Changed subject title.",
            "curated": True
        }
        self.testapp.put(f"{URL}/subjects/{self.non_curated_subject.id}", json.dumps(subject), headers=self.headers, status=self.expected_status['put'])

    def test_subject_post(self):
        subject = {
            "name": "Test subject with spaces and utf-8 chars αℤ"
        }
        self.testapp.post(f'{URL}/subjects', json.dumps(subject), headers=self.headers, status=self.expected_status['post'])

    def test_subject_delete(self):
        subject = {
            "name": "Test subject with spaces and utf-8 chars αℤ"
        }
        self.testapp.delete(f'{URL}/subjects/{self.non_curated_subject.id}', json.dumps({
            'migrate': True,
            'migration_target_id': self.subjects[0].id
        }), headers=self.headers, status=self.expected_status['delete'])


class StudentLoggedInTests(BaseTests):
    expected_status = {
        'get_collection': 200,
        'get': 403,
        'put': 403,
        'post': 403,
        'delete': 403,
    }

    def setUp(self):
        super().setUp()
        self.headers = authenticate_testapp(self.testapp, TESTUSERS["user@muesli.org"])

    def test_subject_get_own(self):
        self.testapp.get(f"{URL}/subjects/{self.user.subjects[0].id}", headers=self.headers, status=200)


class AdminLoggedInTests(StudentLoggedInTests):
    expected_status = {
        'get_collection': 200,
        'get': 200,
        'put': 200,
        'post': 200,
        'delete': 200,
    }

    def setUp(self):
        super().setUp()
        self.headers = authenticate_testapp(self.testapp, TESTUSERS["admin@muesli.org"])
