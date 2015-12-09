import certifi
from geventhttpclient import HTTPClient
import gpsoauth
import urllib
import json
import uuid

SJ_DOMAIN = "mclients.googleapis.com"
SJ_URL = "/sj/v1.11"


def encode(values):
    try:
        for k, v in values.iteritems():
            values[k] = unicode(v).encode("utf-8")
    except Exception:
        pass
    return urllib.urlencode(values)


class Mobileclient(object):

    def __init__(self):
        self._auth = None
        self._sj_client = HTTPClient.from_url(
            "https://{0}{1}".format(SJ_DOMAIN, SJ_URL),
            concurrency=20,
            network_timeout=15,
            ssl_options={
                "ca_certs": certifi.where(),
            })
        self._pl_client = HTTPClient.from_url(
            "https://{0}{1}".format(SJ_DOMAIN, SJ_URL),
            concurrency=1,
            network_timeout=120,
            ssl_options={
                "ca_certs": certifi.where(),
            })

    def login(self, username, password):
        android_id = "asdkfjaj"
        res = gpsoauth.perform_master_login(username, password, android_id)

        if "Token" not in res:
            return False

        self._master_token = res['Token']
        res = gpsoauth.perform_oauth(
            username, self._master_token, android_id,
            service='sj', app='com.google.android.music',
            client_sig='38918a453d07199354f8b19af05ec6562ced5788')
        if 'Auth' not in res:
            return False
        self._auth = res["Auth"]
        self.is_authenticated = True
        return True

    def search_all_access(self, search_query, max_results=1):
        params = {"q": search_query, "max_items": max_results}
        query = encode(params)
        url = "/query?{0}".format(query)
        data = self._http_get(url)
        return data

    def find_best_track(self, search_query):
        data = self.search_all_access(search_query)
        if "entries" not in data:
            return None
        for entry in data["entries"]:
            if entry["type"] == "1":
                return entry["track"]
        return None

    def create_playlist(self, name, public=False):
        mutations = build_create_playlist(name, public)
        data = self._pl_http_post("/playlistbatch?alt=json", {
            "mutations": mutations,
        })
        return data["mutate_response"][0]["id"]  # playlist_id

    def add_songs_to_playlist(self, playlist_id, track_ids):
        mutations = build_add_tracks(playlist_id, track_ids)
        self._pl_http_post("/plentriesbatch?alt=json", {
            "mutations": mutations,
        })

    def _http_get(self, url):
        headers = {
            "Authorization": "GoogleLogin auth={0}".format(self._auth),
            "Content-type": "application/json",
        }
        res = self._sj_client.get(
            SJ_URL + url,
            headers=headers
        )
        body = res.read()
        data = json.loads(body)
        return data

    def _pl_http_post(self, url, data):
        data = json.dumps(data)
        headers = {
            "Authorization": "GoogleLogin auth={0}".format(self._auth),
            "Content-type": "application/json",
        }
        res = self._pl_client.post(
            SJ_URL + url,
            body=data,
            headers=headers
        )
        body = res.read()
        data = json.loads(body)
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
    return [{
        "create": {
            "creationTimestamp": "-1",
            "deleted": False,
            "lastModifiedTimestamp": 0,
            "name": name,
            "type": "USER_GENERATED",
            "accessControlled": public,
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
