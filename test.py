import unittest
import sys

from muesli.tests import functionalTests

loader = unittest.TestLoader()

if len(sys.argv) > 1:
	loader.testMethodPrefix = sys.argv[1]

suites = [loader.loadTestsFromModule(functionalTests),
	#unittest.TestLoader().loadTestsFromTestCase(functionalTests.OrigDatabaseTests),
	#unittest.TestLoader().loadTestsFromTestCase(functionalTests.BaseTests),
	]

for suite in suites:
	unittest.TextTestRunner(verbosity=2).run(suite)
