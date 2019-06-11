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
from decimal import Decimal

def d(f):
    return Decimal(str(f))

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
        self.assertEqual(self.parser.calculate({'$0': d(0.5)}), 0)
        self.assertEqual(self.parser.calculate({'$0': 1}), 1)
        self.assertEqual(self.parser.calculate({'$0': d(1.5)}), 1)
        self.assertEqual(self.parser.calculate({'$0': None}), None)
        self.parser.parseString('cases($0,5,14,4,19,3,24.5,2,29,1)')
        self.assertEqual(self.parser.calculate({'$0': 21}), 3)

    def test_parser_cases1(self):
        self.parser.parseString('cases1($0, 2, 4, 6, 8)')
        self.assertEqual(self.parser.calculate({'$0': 0}), 5)
        self.assertEqual(self.parser.calculate({'$0': d(1.5)}), 5)
        self.assertEqual(self.parser.calculate({'$0': 2}), 4)
        self.assertEqual(self.parser.calculate({'$0': 4}), 3)
        self.assertEqual(self.parser.calculate({'$0': 6}), 2)
        self.assertEqual(self.parser.calculate({'$0': 8}), 1)
        self.assertEqual(self.parser.calculate({'$0': None}), None)

    def test_parser_cases3(self):
        self.parser.parseString('cases3($0,30,34,38,42,46,50,54,58,62,66)')
        self.assertEqual(self.parser.calculate({'$0': 0}), 5)
        self.assertEqual(self.parser.calculate({'$0': 7}), 5)
    def test_parser_cases333(self):
        self.parser.parseString('cases333($0,30,34,38,42,46,50,54,58,62,66)')
        self.assertEqual(self.parser.calculate({'$0': 0}), 5)
        self.assertEqual(self.parser.calculate({'$0': 7}), 5)
        self.assertAlmostEqual(self.parser.calculate({'$0': 34}), d(11.0/3))

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
    def test_parser_round3down(self):
        self.parser.parseString('round3down($0)')
        self.assertEqual(self.parser.calculate({'$0': 5}), 5)
        self.assertEqual(self.parser.calculate({'$0': d(4.1)}), 5)
        self.assertEqual(self.parser.calculate({'$0': d(4.0)}), 4)
        self.assertEqual(self.parser.calculate({'$0': d(1.32)}), 1)
        self.assertEqual(self.parser.calculate({'$0': d(1.33)}), 1)
        self.assertEqual(self.parser.calculate({'$0': d(1.34)}), d(1.3))
        self.assertEqual(self.parser.calculate({'$0': None}), None)
        #0.3 to next step
        for step in [1.0, 2.0, 3.0]:
            self.assertEqual(self.parser.calculate({'$0': d(step)}), d(step))
            self.assertEqual(self.parser.calculate({'$0': d(step+0.1)}), d(step))
            self.assertEqual(self.parser.calculate({'$0': d(step+0.32)}), d(step))
        #0.3 to next step
        for step in [1.3, 2.3, 3.3]:
            self.assertAlmostEqual(self.parser.calculate({'$0': d(step)}), d(step-0.3))
            self.assertAlmostEqual(self.parser.calculate({'$0': d(step+0.033)}), d(step-0.3))
            self.assertEqual(self.parser.calculate({'$0': d(step+0.034)}), d(step))
            self.assertEqual(self.parser.calculate({'$0': d(step+0.365)}), d(step))
        #0.4 to next step
        for step in [1.7, 2.7, 3.7]:
            self.assertEqual(self.parser.calculate({'$0': d(step)}), d(step))
            self.assertEqual(self.parser.calculate({'$0': d(step-0.03)}), d(step))
            self.assertAlmostEqual(self.parser.calculate({'$0': d(step-0.04)}), d(step-0.4))
            self.assertEqual(self.parser.calculate({'$0': d(step+0.1)}), d(step))
            self.assertEqual(self.parser.calculate({'$0': d(step+0.29)}), d(step))
    def test_parser_schmidtsche_weltformel(self):
        for weltformel in ['cases3(-1*$0-2*$1,-36,-35,-32,-29,-26,-23,-20,-17,-14,-11)',
                        'round3down(($0+2*$1)/9)']:
            self.parser.parseString(weltformel)
            #Trivialitäten sind auch wichtig
            self.assertEqual(self.parser.calculate({'$0': d(15), '$1': d(15)}), 5)
            self.assertEqual(self.parser.calculate({'$0': d(12), '$1': d(12)}), 4)
            self.assertEqual(self.parser.calculate({'$0': d(11), '$1': d(11)}), d(3.7))
            self.assertEqual(self.parser.calculate({'$0': d(10), '$1': d(10)}), d(3.3))
            self.assertEqual(self.parser.calculate({'$0': d(9), '$1': d(9)}), 3)
            self.assertEqual(self.parser.calculate({'$0': d(8), '$1': d(8)}), d(2.7))
            self.assertEqual(self.parser.calculate({'$0': d(7), '$1': d(7)}), d(2.3))
            self.assertEqual(self.parser.calculate({'$0': d(6), '$1': d(6)}), d(2.0))
            self.assertEqual(self.parser.calculate({'$0': d(5), '$1': d(5)}), d(1.7))
            self.assertEqual(self.parser.calculate({'$0': d(4), '$1': d(4)}), d(1.3))
            self.assertEqual(self.parser.calculate({'$0': d(3), '$1': d(3)}), d(1.0))
            #MC 5 AT 4: gewichtetes Mittel: 1/3 * (5 + 2*4)= 4 1/3: nicht bestanden 5
            self.assertEqual(self.parser.calculate({'$0': d(5*3), '$1': d(4*3)}), 5)
            #MC 2,0 AT 5: gewichtetes Mittel 4 bestanden mit Note 4
            self.assertEqual(self.parser.calculate({'$0': d(2*3), '$1': d(5*3)}), 4)
            #MC 1, AT 3 gewichtetes Mittel  2 1/3 = bestanden mit Note 2,3
            self.assertEqual(self.parser.calculate({'$0': d(1*3), '$1': d(3*3)}), d(2.3))
            #MC 2, AT 3 gewichtetes Mittel  2 2/3 = bestanden mit Note 2,7
            self.assertEqual(self.parser.calculate({'$0': d(2*3), '$1': d(3*3)}), d(2.7))
            #MC 3 1/3, AT 3: gewichtetes Mittel 3,1... gerundet auf Gesamtnote 3.0
            self.assertEqual(self.parser.calculate({'$0': d(10), '$1': d(3*3)}), 3)
            #MC 3, AT 3 1/3: gewichtetes Mittel 3,2... gerundet auf Gesamtnote 3.0
            self.assertEqual(self.parser.calculate({'$0': d(3*3), '$1': d(10)}), 3)
            #MC 2, AT 2 2/3: gewichtetes Mittel 2,4... gerundet auf Gesamtnote 2,3
            self.assertEqual(self.parser.calculate({'$0': d(2*3), '$1': d(8)}), d(2.3))
            #MC 1 1/3, AT 1: gewichtetes Mittel 1,1... gerundet auf Gesamtnote 1,0
            self.assertEqual(self.parser.calculate({'$0': d(4), '$1': d(1*3)}), 1)
