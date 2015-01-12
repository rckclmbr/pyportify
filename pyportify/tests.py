import unittest
from pyportify import views


class UserScopeTest(unittest.TestCase):

    def test_user_scope(self):
        scope = views.user_scope

        assert not scope.google_loggedin()
        assert not scope.spotify_loggedin()
