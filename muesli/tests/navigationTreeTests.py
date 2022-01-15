import muesli.web
from pyramid import testing
from pyramid.testing import DummyRequest
from muesli.tests import functionalTests
from muesli.web.navigation_tree import create_navigation_tree

class BaseTests(functionalTests.BaseTests):
    def setUp(self):
        functionalTests.BaseTests.setUp(self)
        self.config = testing.setUp()
        muesli.web.populate_config(self.config)
    def test_navigation_tree_empty_login(self):
        request = DummyRequest()
        request.user = None
        tree = create_navigation_tree(request)
        self.assertFalse(tree.children)

