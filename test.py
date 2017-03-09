import unittest
import sys
import muesli.tests

loader = unittest.TestLoader()

if len(sys.argv) > 1:
	loader.testMethodPrefix = sys.argv[1]

names = ['muesli.tests.functionalTests',
	     'muesli.tests.rootTests',
	     'muesli.tests.userTests',
	     'muesli.tests.lectureTests',
	     'muesli.tests.examTests',
	     'muesli.tests.gradingTests',
	     'muesli.tests.tutorialTests',
	     'muesli.tests.parserTests',
	     'muesli.tests.utilsTests',
		 ]

suites = [loader.loadTestsFromNames(names),
	]

for suite in suites:
	unittest.TextTestRunner(verbosity=2).run(suite)
