import json
import uuid
import urllib
import gmusicapi
import functools

import asyncio
from pyportify import gpsoauth

SJ_DOMAIN = "mclients.googleapis.com"
SJ_URL = "/sj/v1.11"

FULL_SJ_URL = "https://{0}{1}".format(SJ_DOMAIN, SJ_URL)


def encode(values):
    return urllib.parse.urlencode(values)


class AuthenticationError(ValueError):
    pass


class Mobileclient(object):

    def __init__(self, session, token=None, max_in_flight=1):
        self.token = token
        self.session = session

        self._loop = asyncio.get_event_loop()
        self._sync_gmapi = gmusicapi.Mobileclient()

        self.limiter = asyncio.Semaphore(value=max_in_flight)
        self.is_not_limited = asyncio.Event()
        self.is_not_limited.set()

    @asyncio.coroutine
    def login(self, username, password, android_id="asdkfjaj"):
        res = gpsoauth.perform_master_login(username, password, android_id)
        if "Token" not in res:
            raise AuthenticationError(username)
        self._master_token = res['Token']

        res = gpsoauth.perform_oauth(
            username,
            self._master_token,
            android_id,
            service='sj',
            app='com.google.android.music',
            client_sig='38918a453d07199354f8b19af05ec6562ced5788'
        )
        if 'Auth' not in res:
            raise AuthenticationError(username)
        self.token = res["Auth"]

        meth = functools.partial(self._sync_gmapi.login, username, password, android_id)
        yield from self._loop.run_in_executor(None, meth)

        return self.token

    @asyncio.coroutine
    def search_all_access(self, search_query, max_results=30):
        params = {"q": search_query, "max_items": max_results, 'type': 1}
        query = encode(params)
        url = "/query?{0}".format(query)
        data = yield from self._http_get(url)
        return data

    @asyncio.coroutine
    def find_best_track(self, search_query):
        data = yield from self.search_all_access(search_query)
        if "entries" not in data:
            return None
        for entry in data["entries"]:
            if entry["type"] == "1":
                return entry["track"]
        return None

    @asyncio.coroutine
    def cache_playlists(self):
        meth = functools.partial(self._sync_gmapi.get_all_user_playlist_contents)
        self._playlists = yield from self._loop.run_in_executor(None, meth)

    @asyncio.coroutine
    def get_cached_playlist(self, name=None, playlist_id=None):
        terms = dict(
            name=name,
            id=playlist_id,
        )

        for pl in self._playlists:
            for k, v in terms.items():
                if pl[k] == v:
                    return pl

    @asyncio.coroutine
    def delete_playlist(self, playlist_id):
        meth = functools.partial(self._sync_gmapi.delete_playlist, playlist_id)
        ret = yield from self._loop.run_in_executor(None, meth)
        return ret

    @asyncio.coroutine
    def ensure_songs_in_playlist(self, playlist_id, track_ids):
        playlist = yield from self.get_cached_playlist(playlist_id)
        existing_track_ids = []
        if playlist:
            existing_track_ids.extend([t['id'] for t in playlist['tracks']])

        # Without order, there is chaos
        missing_track_ids = [t for t in track_ids if not t in existing_track_ids]
        if not missing_track_ids:
            return

        final_track_ids = existing_track_ids + missing_track_ids
        # Google supports a max of 1000 per playlist
        final_track_ids = final_track_ids[:1000]

        # Need the output so be sync for now
        added_track_ids = yield from self.add_songs_to_playlist(playlist_id, missing_track_ids)
        # meth = functools.partial(self._sync_gmapi.add_songs_to_playlist, playlist_id, missing_track_ids)
        # added_track_ids = yield from self._loop.run_in_executor(None, meth)

        # if len(added_track_ids) != len(missing_track_ids):
        #     missing = set(missing_track_ids) - added_track_ids
        #     raise ValueError(
        #         "Got back %d added track ids when we wanted %d. Missing: %s" % (len(added_track_ids), missing)
        #     )

        return added_track_ids

    @asyncio.coroutine
    def create_playlist(self, name, public=False):
        mutations = build_create_playlist(name, public)
        data = yield from self._http_post("/playlistbatch?alt=json", {"mutations": mutations,})
        return data["mutate_response"][0]["id"]  # playlist_id

    @asyncio.coroutine
    def add_songs_to_playlist(self, playlist_id, track_ids):
        mutations = build_add_tracks(playlist_id, track_ids)
        yield from self._http_post("/plentriesbatch?alt=json", {"mutations": mutations,})

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
        yield from self.limiter.acquire()
        try:
            yield from self.is_not_limited.wait()

            headers = {
                "Authorization": "GoogleLogin auth={0}".format(self.token),
                "Content-type": "application/json",
            }

            res = yield from self.session.request('GET', FULL_SJ_URL + url, headers=headers)
            data = yield from res.json()

            if "error" in data:
                if data['error']['status'] in (429, 401):
                    log.warning('Google API limit exceeded: %s', data['error'].get('message'))
                    yield from self._backoff()
                    data = yield from self._http_get(url)
                else:
                    raise Exception("Error: {0}, url: {1}".format(data, url))
        finally:
            self.limiter.release()
        return data

    @asyncio.coroutine
    def _http_post(self, url, data):
        yield from self.limiter.acquire()
        try:
            yield from self.is_not_limited.wait()

            data = json.dumps(data)
            headers = {
                "Authorization": "GoogleLogin auth={0}".format(self.token),
                "Content-type": "application/json",
            }
            res = yield from self.session.request(
                'POST',
                FULL_SJ_URL + url,
                data=data,
                headers=headers,
            )
            data = yield from res.json()

            if "error" in data:
                if data['error']['status'] in (429, 401):
                    log.warning('Google API limit exceeded: %s', data['error'].get('message'))
                    yield from self._backoff()
                    data = yield from self._http_get(url)
                else:
                    raise Exception("Error: {0}, url: {1}".format(data, url))
        finally:
            self.limiter.release()
        return data


def build_add_tracks(playlist_id, track_ids):
    mutations = []
    prev_id = ""
    cur_id = str(uuid.uuid4())
    next_id = str(uuid.uuid4())

    for i, track_id in enumerate(track_ids):
        details = {
            "create": {
                "clientId": cur_id,
                "creationTimestamp": -1,
                "deleted": False,
                "lastModifiedTimestamp": "0",
                "playlistId": playlist_id,
                "source": 1,
                "trackId": track_id,
            }
        }

        if track_id.startswith("T"):
            details["create"]["source"] = 2  # AA track

        if i > 0:
            details["create"]["precedingEntryId"] = prev_id

        if i < len(track_ids) - 1:
            details["create"]["followingEntryId"] = next_id

        mutations.append(details)

        prev_id = cur_id
        cur_id = next_id
        next_id = str(uuid.uuid4())
    return mutations


def build_create_playlist(name, public):
    return [
        {
            "create": {
                "creationTimestamp": "-1",
                "deleted": False,
                "lastModifiedTimestamp": 0,
                "name": name,
                "type": "USER_GENERATED",
                "accessControlled": public,
            }
        }
    ]


def parse_auth_response(s):
    # SID=DQAAAGgA...7Zg8CTN
    # LSID=DQAAAGsA...lk8BBbG
    # Auth=DQAAAGgA...dk3fA5N
    res = {}
    for line in s.split("\n"):
        if not line:
            continue
        k, v = line.split("=", 1)
        res[k] = v
    return res
