import muesli.web
from pyramid import testing
from pyramid.testing import DummyRequest
from muesli.tests import functionalTests
from muesli.web import subscribe
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

class PopulatedTests(functionalTests.PopulatedTests):
    def setUp(self):
        functionalTests.BaseTests.setUp(self)
        self.config = testing.setUp()
        muesli.web.populate_config(self.config)
    def test_navigation_tree_no_tutorials(self):
        request = DummyRequest()
        request.user = self.user_without_lecture
        tree = create_navigation_tree(request)
        self.assertFalse(tree.children)
    def test_navigation_tree_has_tutorials(self):
        subscribe(db=self.session, user=self.user, tutorial=self.tutorial)
        self.tutorial.lecture.term = muesli.utils.getSemesterLimit()
        request = DummyRequest()
        request.user = self.user
        tree = create_navigation_tree(request)
        self.assertEqual(len(tree.children), 1)
        self.assertEqual(len(tree.children[0].children), 1)
        self.assertIn(self.tutorial.lecture.name, tree.children[0].children[0].label)
    def test_navigation_tree_tutor(self):
        self.tutorial.lecture.term = muesli.utils.getSemesterLimit()
        request = DummyRequest()
        request.user = self.tutor
        tree = create_navigation_tree(request)
        self.assertEqual(len(tree.children), 1)
        self.assertIn("Vorlesungsorganisation", tree.children[0].label)
        self.assertEqual(len(tree.children[0].children), 1)
        self.assertIn(self.tutorial.lecture.name, tree.children[0].children[0].label)
        self.assertEqual(len(tree.children[0].children[0].children), 3)
        self.assertIn("Übungsgruppen", tree.children[0].children[0].children[0].label)
