# -*- coding: utf-8 -*-
#
# muesli/tests/parserTests.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2012, Matthias Kuemmerer <matthias (at) matthias-k.org>
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
import muesli.utils as utils


class ContextTests(unittest.TestCase):
    def test_list_strings(self):
        self.assertEqual(utils.list_strings([]), '')
        self.assertEqual(utils.list_strings(['test1']), 'test1')
        self.assertEqual(utils.list_strings(['test1', 'test2']), 'test1 und test2')
        self.assertEqual(utils.list_strings(['test1', 'test2', 'test3']), 'test1, test2 und test3')
        self.assertEqual(utils.list_strings(['test1', 'test2', 'test3', 'test4']), 'test1, test2, test3 und test4')
