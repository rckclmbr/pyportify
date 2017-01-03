import asyncio
import urllib
import os
import logging

log = logging.getLogger(__name__)


class SpotifyQuery():

    def __init__(self, i, sp_playlist_uri, sp_track, track_count):
        self.i = i
        self.playlist_uri = sp_playlist_uri
        self.sp_track = sp_track
        self.track_count = track_count

    def search_query(self):
        if "artists" in self.sp_track['track']:
            sp_artist = self.sp_track['track']['artists'][0]
            search_query = "{0} - {1}".format(
                sp_artist['name'],
                self.sp_track['track']['name'],
            )
        else:
            search_query = "{0}".format(self.sp_track['name'])
        return search_query


def encode(values):
    return urllib.parse.urlencode(values)


class SpotifyClient(object):
    _api_root = 'https://api.spotify.com/v1'

    def __init__(self, session, token=None, max_in_flight=1):
        self.session = session
        self.token = token

        self.limiter = asyncio.Semaphore(value=max_in_flight)
        self.is_not_limited = asyncio.Event()
        self.is_not_limited.set()

    def _gen_url(self, url):
        if not url.startswith('http'):
            url = '%s%s' % (self._api_root, url)
        return url

    @asyncio.coroutine
    def loggedin(self):
        playlists = yield from self._http_get('/me/playlists')
        if "error" in playlists:
            return False
        return True

    @asyncio.coroutine
    def fetch_spotify_playlists(self):
        ret_playlists = [{
            "name": "Saved Tracks",
            "uri": "saved",
            "type": "custom",
        }]

        url = '/me/playlists'
        playlists = yield from self._http_get_all(url)
        ret_playlists.extend(playlists)
        return ret_playlists

    @asyncio.coroutine
    def _http_get_all(self, url):
        ret = []
        while True:
            data = yield from self._http_get(url)
            url = data['next']
            ret.extend(data['items'])
            if url is None:
                break
        return ret

    @asyncio.coroutine
    def fetch_saved_tracks(self):
        url = '/me/tracks'
        tracks = yield from self._http_get_all(url)
        return tracks

    @asyncio.coroutine
    def fetch_playlist_tracks(self, uri):
        if uri == 'saved':
            ret = yield from self.fetch_saved_tracks()
            return ret

        # spotify:user:<user_id>:playlist:<playlist_id>
        parts = uri.split(':')
        user_id = parts[2]
        playlist_id = parts[-1]

        url = '/users/{0}/playlists/{1}/tracks' \
            .format(user_id, playlist_id)
        ret = yield from self._http_get_all(url)
        return ret

    @asyncio.coroutine
    def fetch_playlist(self, uri):
        if uri == 'saved':
            return {
                'name': 'Saved Tracks',
                'uri': uri,
            }
        parts = uri.split(':')  # spotify:user:<user_id>:playlist:<playlist_id>
        user_id = parts[2]
        playlist_id = parts[-1]

        url = '/users/{0}/playlists/{1}'.format(
            user_id,
            playlist_id,
        )
        ret = yield from self._http_get(url)
        return ret

    @asyncio.coroutine
    def _backoff(self, timeout=10):
        if not self.is_not_limited.is_set():
            yield from self.is_not_limited.wait()
        else:
            log.debug('Hit API limit; waiting %d seconds until trying again.', timeout)
            self.is_not_limited.clear()
            yield from asyncio.sleep(timeout)
            self.is_not_limited.set()

    @asyncio.coroutine
    def _http_get(self, url):
        url = self._gen_url(url)

        yield from self.limiter.acquire()
        try:
            yield from self.is_not_limited.wait()

            headers = {
                'Authorization': 'Bearer {0}'.format(self.token),
                "Content-type": "application/json",
            }

            res = yield from self.session.request(
                'GET',
                url,
                headers=headers,
                skip_auto_headers=['Authorization'],
            )
            data = yield from res.json()

            if "error" in data:
                if data['error']['status'] == 429:
                    log.warning('Spotify API limit exceeded: %s', data['error'].get('message'))
                    yield from self._backoff()
                    data = yield from self._http_get(url)
                else:
                    raise Exception("Error: {0}, url: {1}".format(data, url))
        finally:
            self.limiter.release()
        return data
