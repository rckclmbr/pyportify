import unittest
from pyportify import app
from pyportify.serializers import Track
from pyportify.util import find_closest_match


class UserScopeTest(unittest.TestCase):

    def test_user_scope(self):
        scope = app.user_scope

        assert not scope.google_token
        assert not scope.spotify_token


class TrackMatchTest(unittest.TestCase):

    def test_artist_match(self):
        target_artist = "Target"
        target_name = "Songs to Test By"
        expected_id = 1

        target_track = Track(
            artist=target_artist,
            name=target_name
        )
        expected_match = Track(
            artist=target_artist,
            name=target_name,
            track_id=expected_id
        )
        unexpected_match = Track(
            artist="Not Me!",
            name=target_name
        )

        match = find_closest_match(target_track, [
            expected_match,
            unexpected_match
        ])

        assert match.track_id == expected_id

    def test_artist_match_close_track_name(self):
        target_artist = "Target"
        target_name = "Songs to Test By"
        expected_id = 1

        target_track = Track(
            artist=target_artist,
            name=target_name
        )
        expected_match = Track(
            artist=target_artist,
            name="Songs to Test With",
            track_id=expected_id
        )
        unexpected_match = Track(
            artist="Not Me, but my track name is closer!",
            name=target_name
        )

        match = find_closest_match(target_track, [
            expected_match,
            unexpected_match
        ])

        assert match.track_id == expected_id

    def test_close_artist_and_name_match(self):
        target_artist = "Target"
        target_name = "Songs to Test By"
        expected_id = 1

        target_track = Track(
            artist=target_artist,
            name=target_name
        )
        expected_match = Track(
            artist="Targ",
            name="Songs to Test With",
            track_id=expected_id
        )
        unexpected_match = Track(
            artist="Not Me!",
            name=target_name
        )

        match = find_closest_match(target_track, [
            expected_match,
            unexpected_match
        ])

        assert match.track_id == expected_id

    def test_multi_artist_match(self):
        target_artist = "Target"
        target_name = "Songs to Test By"
        expected_id = 1

        target_track = Track(
            artist=target_artist,
            name=target_name
        )
        expected_match = Track(
            artist=target_artist,
            name=target_name,
            track_id=expected_id
        )
        un_exp_match1 = Track(
            artist=target_artist,
            name="Songs to Test With?"
        )
        un_exp_match2 = Track(
            artist=target_artist,
            name="Songs to Test With! - ft. Test"
        )
        un_exp_match3 = Track(
            artist="Not Me!",
            name=target_name
        )

        match = find_closest_match(target_track, [
            expected_match,
            un_exp_match1,
            un_exp_match2,
            un_exp_match3
        ])

        assert match.track_id == expected_id
