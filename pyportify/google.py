import json
import uuid
import urllib
from uuid import getnode as getmac

import asyncio
from pyportify import gpsoauth

SJ_DOMAIN = "mclients.googleapis.com"
SJ_URL = "/sj/v2.5"

FULL_SJ_URL = "https://{0}{1}".format(SJ_DOMAIN, SJ_URL)


def encode(values):
    return urllib.parse.urlencode(values)


class Mobileclient(object):

    def __init__(self, session, token=None):
        self.token = token
        self.session = session

    @asyncio.coroutine
    def login(self, username, password):
        android_id = _get_android_id()
        res = gpsoauth.perform_master_login(username, password, android_id)

        if "Token" not in res:
            return None

        self._master_token = res['Token']
        res = gpsoauth.perform_oauth(
            username, self._master_token, android_id,
            service='sj', app='com.google.android.music',
            client_sig='38918a453d07199354f8b19af05ec6562ced5788')
        if 'Auth' not in res:
            return None
        self.token = res["Auth"]
        return self.token

    @asyncio.coroutine
    def search_all_access(self, search_query, max_results=30):
        data = yield from self._http_get("/query", {
            "q": search_query,
            "max-results": max_results,
            'ct': '1,2,3,4,6,7,8,9',
        })
        return data

    @asyncio.coroutine
    def find_best_track(self, search_query):
        track = None
        for i in range(0, 2):
            data = yield from self.search_all_access(search_query)
            if 'suggestedQuery' in data:
                data = yield from self.search_all_access(
                    data['suggestedQuery'])
            if "entries" not in data:
                continue
            for entry in data["entries"]:
                if entry["type"] == "1":
                    track = entry["track"]
                    break
            if track:
                break
        return track

    @asyncio.coroutine
    def fetch_playlists(self):
        data = yield from self._http_post("/playlistfeed", {})
        # TODO: paging
        return data

    @asyncio.coroutine
    def create_playlist(self, name, public=False):
        mutations = build_create_playlist(name, public)
        data = yield from self._http_post("/playlistbatch", {
            "mutations": mutations,
        })
        res = data["mutate_response"]
        playlist_id = res[0]["id"]
        return playlist_id

    @asyncio.coroutine
    def add_songs_to_playlist(self, playlist_id, track_ids):
        data = {
            "mutations": build_add_tracks(playlist_id, track_ids),
        }
        res = yield from self._http_post('/plentriesbatch', data)
        added_ids = [e['id'] for e in res['mutate_response']]
        return added_ids

    @asyncio.coroutine
    def _http_get(self, url, params):
        headers = {
            "Authorization": "GoogleLogin auth={0}".format(self.token),
            "Content-type": "application/json",
        }

        merged_params = params.copy()
        merged_params.update({
            'tier': 'aa',
            'hl': 'en_US',
            'dv': 0,
        })

        res = yield from self.session.request(
            'GET',
            FULL_SJ_URL + url,
            headers=headers,
            params=merged_params,
        )
        data = yield from res.json()
        return data

    @asyncio.coroutine
    def _http_post(self, url, data):
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
            params={
                'tier': 'aa',
                'hl': 'en_US',
                'dv': 0,
                'alt': 'json',
            }
        )
        ret = yield from res.json()
        return ret


def build_add_tracks(playlist_id, track_ids):
    mutations = []
    prev_id = ""
    cur_id = str(uuid.uuid1())
    next_id = str(uuid.uuid1())

    for i, track_id in enumerate(track_ids):
        details = {
            "create": {
                "clientId": cur_id,
                "creationTimestamp": "-1",
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
        next_id = str(uuid.uuid1())
    return mutations


def build_create_playlist(name, public):
    return [{
        "create": {
            "creationTimestamp": "-1",
            "deleted": False,
            "lastModifiedTimestamp": 0,
            "name": name,
            "description": "",
            "type": "USER_GENERATED",
            "shareState": "PUBLIC" if public else "PRIVATE",
        }
    }]


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


def _get_android_id():
    mac_int = getmac()
    if (mac_int >> 40) % 2:
        raise OSError("a valid MAC could not be determined."
                      " Provide an android_id (and be"
                      " sure to provide the same one on future runs).")

    android_id = _create_mac_string(mac_int)
    android_id = android_id.replace(':', '')
    return android_id


def _create_mac_string(num, splitter=':'):
    mac = hex(num)[2:]
    if mac[-1] == 'L':
        mac = mac[:-1]
    pad = max(12 - len(mac), 0)
    mac = '0' * pad + mac
    mac = splitter.join([mac[x:x + 2] for x in range(0, 12, 2)])
    mac = mac.upper()
    return mac
