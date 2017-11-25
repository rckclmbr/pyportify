import urllib


class SpotifyQuery():

    def __init__(self, i, sp_playlist_uri, sp_track, track_count):
        self.i = i
        self.playlist_uri = sp_playlist_uri
        self.sp_track = sp_track
        self.track_count = track_count

    def search_query(self):
        track = self.sp_track.get("track")
        if not track:
            return None

        if "artists" in track:
            sp_artist = track['artists'][0]
            search_query = "{0} - {1}".format(
                sp_artist['name'],
                track['name'])
        else:
            search_query = "{0}".format(self.sp_track['name'])
        return search_query


def encode(values):
    return urllib.parse.urlencode(values)


class SpotifyClient(object):

    def __init__(self, session, token=None):
        self.session = session
        self.token = token

    async def loggedin(self):
        playlists = await self._http_get(
            'https://api.spotify.com/v1/me/playlists')
        if "error" in playlists:
            return False
        return True

    async def fetch_spotify_playlists(self):
        ret_playlists = [{
            "name": "Saved Tracks",
            "uri": "saved",
            "type": "custom"}]

        url = 'https://api.spotify.com/v1/me/playlists'
        playlists = await self._http_get_all(url)
        ret_playlists.extend(playlists)
        return ret_playlists

    async def _http_get_all(self, url):
        ret = []
        while True:
            data = await self._http_get(url)
            url = data['next']
            ret.extend(data['items'])
            if url is None:
                break
        return ret

    async def fetch_saved_tracks(self):
        url = 'https://api.spotify.com/v1/me/tracks'
        tracks = await self._http_get_all(url)
        return tracks

    async def fetch_playlist_tracks(self, uri):
        if uri == 'saved':
            ret = await self.fetch_saved_tracks()
            return ret

        # spotify:user:<user_id>:playlist:<playlist_id>
        parts = uri.split(':')
        user_id = parts[2]
        playlist_id = parts[-1]

        url = 'https://api.spotify.com/v1/users/{0}/playlists/{1}/tracks' \
            .format(user_id, playlist_id)
        ret = await self._http_get_all(url)
        return ret

    async def fetch_playlist(self, uri):
        if uri == 'saved':
            return {'name': 'Saved Tracks',
                    'uri': uri}
        parts = uri.split(':')  # spotify:user:<user_id>:playlist:<playlist_id>
        user_id = parts[2]
        playlist_id = parts[-1]

        url = 'https://api.spotify.com/v1/users/{0}/playlists/{1}'.format(
            user_id, playlist_id)
        ret = await self._http_get(url)
        return ret

    async def _http_get(self, url):
        headers = {"Authorization": "Bearer {0}".format(self.token),
                   "Content-type": "application/json"}
        res = await self.session.request(
            'GET',
            url,
            headers=headers,
            skip_auto_headers=['Authorization'])
        data = await res.json()
        if "error" in data:
            raise Exception("Error: {0}, url: {1}".format(data, url))
        return data
