import unittest
from pyportify import app


class UserScopeTest(unittest.TestCase):

    def test_user_scope(self):
        scope = app.user_scope

        assert not scope.google_token
        assert not scope.spotify_token
