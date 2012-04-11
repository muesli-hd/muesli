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
from muesli.parser import Parser


class ContextTests(unittest.TestCase):
	def setUp(self):
		self.parser = Parser()
		
	def test_parser_add(self):
		self.parser.parseString('1+2')
		self.assertEqual(self.parser.calculate({}), 3)
		self.parser.parseString('$0+$1')
		self.assertEqual(self.parser.calculate({'$0': 1, '$1': 2}), 3)
		#Addition should handle None=0
		self.assertEqual(self.parser.calculate({'$0': 1, '$1': None}), 1)
		#Unless everything is None
		self.assertEqual(self.parser.calculate({'$0': None, '$1': None}), None)

	def test_parser_mul(self):
		self.parser.parseString('2*3')
		self.assertEqual(self.parser.calculate({}), 6)
		self.parser.parseString('$0*$1')
		self.assertEqual(self.parser.calculate({'$0': 2, '$1': 3}), 6)
		#Addition should handle None=0
		self.assertEqual(self.parser.calculate({'$0': 1, '$1': None}), None)
		#Unless everything is None
		self.assertEqual(self.parser.calculate({'$0': None, '$1': None}), None)

	def test_parser_cases(self):
		self.parser.parseString('cases($0, 0, 1, 1)')
		self.assertEqual(self.parser.calculate({'$0': 0}), 0)
		self.assertEqual(self.parser.calculate({'$0': 0.5}), 0)
		self.assertEqual(self.parser.calculate({'$0': 1}), 1)
		self.assertEqual(self.parser.calculate({'$0': 1.5}), 1)
		self.assertEqual(self.parser.calculate({'$0': None}), None)

	def test_parser_cases1(self):
		self.parser.parseString('cases1($0, 2, 4, 6, 8)')
		self.assertEqual(self.parser.calculate({'$0': 0}), 5)
		self.assertEqual(self.parser.calculate({'$0': 1.5}), 5)
		self.assertEqual(self.parser.calculate({'$0': 2}), 4)
		self.assertEqual(self.parser.calculate({'$0': 4}), 3)
		self.assertEqual(self.parser.calculate({'$0': 6}), 2)
		self.assertEqual(self.parser.calculate({'$0': 8}), 1)
		self.assertEqual(self.parser.calculate({'$0': None}), None)

	def test_parser_cases3(self):
		self.parser.parseString('cases3($0,30,34,38,42,46,50,54,58,62,66)')
		self.assertEqual(self.parser.calculate({'$0': 0}), 5)
		self.assertEqual(self.parser.calculate({'$0': 7}), 5)

	def test_parser_min(self):
		self.parser.parseString('min($0)')
		self.assertEqual(self.parser.calculate({'$0': 0}), 0)
		self.assertEqual(self.parser.calculate({'$0': 1}), 1)
		self.assertEqual(self.parser.calculate({'$0': None}), None)
		self.parser.parseString('min($0, $1)')
		self.assertEqual(self.parser.calculate({'$0': 0, '$1': 1}), 0)
		self.assertEqual(self.parser.calculate({'$0': 1, '$1': 0}), 0)
		self.assertEqual(self.parser.calculate({'$0': None, '$1': 1}), 1)
		self.assertEqual(self.parser.calculate({'$0': None, '$1': None}), None)