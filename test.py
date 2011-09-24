import unittest

from muesli.tests import functionalTests

suites = [unittest.TestLoader().loadTestsFromModule(functionalTests),
	#unittest.TestLoader().loadTestsFromTestCase(functionalTests.OrigDatabaseTests),
	#unittest.TestLoader().loadTestsFromTestCase(functionalTests.BaseTests),
	]

for suite in suites:
	unittest.TextTestRunner(verbosity=2).run(suite)
