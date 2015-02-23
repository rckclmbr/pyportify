import os
import threading

from gevent import monkey

from flask import Flask, Response, jsonify, send_from_directory, request
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from gmusicapi import Mobileclient
import spotify

monkey.patch_all()

app = Flask(__name__)
app.config['PORT'] = 3132
# app.config['DEBUG'] = True

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, "static")
SPOTIFY_APPKEY = os.path.join(BASE_DIR, "spotify_appkey.key")


class UserScope(object):

    def __init__(self):
        self.googleapi = Mobileclient()

        config = spotify.Config()
        config.cache_location = "tmp"
        config.load_application_key_file(SPOTIFY_APPKEY)
        self.spotify_session = spotify.Session(config)
        self.loop = spotify.EventLoop(self.spotify_session)
        self.logged_in_event = threading.Event()
        self._google_loggedin = False

    def _logged_in_listener(self, session, error_type):
        if error_type is spotify.ErrorType.OK:
            # Now wait for the connection_state_listener to be state LOGGED_IN
            return
        # Otherwise, there's a login error and we can return immediately
        self.logged_in_event.set()

    def _connection_state_listener(self, session):
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            self.logged_in_event.set()

    def start(self):
        self.loop.start()
        self.spotify_session.on(spotify.SessionEvent.LOGGED_IN,
                                self._logged_in_listener)
        self.spotify_session.on(spotify.SessionEvent.CONNECTION_STATE_UPDATED,
                                self._connection_state_listener)

    def google_login(self, username, password):
        self._google_loggedin = self.googleapi.login(username, password)
        return self._google_loggedin

    def spotify_login(self, username, password):
        self.logged_in_event.clear()
        user_scope.spotify_session.login(username, password)
        self.logged_in_event.wait()
        return self.spotify_session.user

    def spotify_loggedin(self):
        return self.spotify_session.user

    def google_loggedin(self):
        return self._google_loggedin


user_scope = UserScope()
user_scope.start()


@app.route("/google/login", methods=["POST", ])
def google_login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user_scope.google_login(email, password)
    if not user_scope.google_loggedin():
        return jsonify(dict(
            status=400,
            message="login failed.",
        ))

    return jsonify(dict(
        status=200,
        message="login successful."
    ))


@app.route("/spotify/login", methods=["POST", ])
def spotify_login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user_scope.spotify_login(username, password)
    if not user_scope.spotify_loggedin():
        return jsonify(dict(
            status=400,
            message="login failed.",
        ))
    return jsonify(dict(
        status=200,
        message="login successful."
    ))


@app.route("/portify/transfer/start", methods=["POST"])
def transfer_start():

    lists = request.get_json()

    if not user_scope.google_loggedin():
        return jsonify({"status": 401, "message": "Google: not logged in."})

    if not user_scope.spotify_loggedin():
        return jsonify({"status": 402, "message": "Spotify: not logged in."})

    if not lists:
        return jsonify({"status": 403,
                        "message": "Please select at least one playlist."})

    transfer_playlists(lists)
    return jsonify({"status": 200, "message": "transfer will start."})


@app.route("/spotify/playlists")
def spotify_playlists():
    ret_playlists = fetch_spotify_playlists()
    return jsonify({"status": 200, "message": "ok", "data": ret_playlists})


def fetch_spotify_playlists():
    container = user_scope.spotify_session.playlist_container
    playlists = container.load()

    ret_playlists = [{
        "name": "Starred Tracks",
        "uri": "spotify:user:%s:playlist:starred"
               % user_scope.spotify_session.remembered_user_name,
    }]

    for playlist in playlists:
        if isinstance(playlist, spotify.PlaylistFolder):
            continue
        playlist.load()
        plist = {
            "name": playlist.name,
            "uri": playlist.link.uri,
        }
        ret_playlists.append(plist)
    return ret_playlists


@app.route("/", defaults={'path': 'index.html'})
@app.route("/<path:path>")
def base(path):
    emit("test", {"type": "playlist_length"})
    return send_from_directory(STATIC_ROOT, path)


def transfer_playlists(playlists):
    s = user_scope.spotify_session
    g = user_scope.googleapi
    for d_list in playlists:
        if ":starred" in d_list["uri"]:
            sp_playlist = s.get_starred()
            sp_playlist.name = 'Starred Tracks'
        else:
            sp_playlist = s.get_playlist(d_list["uri"])
        gm_track_ids = []

        playlist_name_ascii = sp_playlist.name.encode('utf8', 'replace')
        print "Gathering tracks for playlist %s" % playlist_name_ascii

        track_count = len(sp_playlist.tracks)
        playlist_json = {
            "playlist": {
                "uri": d_list["uri"],
                "name": sp_playlist.name,
            },
            "name": sp_playlist.name,
        }
        emit("portify", {"type": "playlist_length",
                         "data": {"length": track_count}})
        emit("portify", {"type": "playlist_started",
                         "data": playlist_json})
        for i, sp_track in enumerate(sp_playlist.tracks):
            sp_track.load()
            if sp_track.artists:
                sp_artist = sp_track.artists[0]
            else:
                sp_artist = None

            search_query = "%s - %s" % (sp_artist.name, sp_track.name)
            search_query_ascii = search_query.encode("utf-8", "replace")
            search_results = g.search_all_access(search_query, max_results=1)
            songs = search_results.get("song_hits")
            if songs:
                gm_track_id = songs[0]["track"]["nid"]
                gm_track_ids.append(gm_track_id)
                print "(%s/%s) Found '%s' in Google Music" \
                      % (i+1, track_count, search_query_ascii)
                emit("gmusic", {
                    "type": "added",
                    "data": {
                        "spotify_track_uri": d_list["uri"],
                        "spotify_track_name": sp_track.name,
                        "found": True,
                        "karaoke": False,
                    }
                })
            else:
                print "(%s/%s) No match found for '%s'" \
                      % (i+1, track_count, search_query_ascii)
                emit("gmusic", {
                    "type": "not_added",
                    "data": {
                        "spotify_track_uri": d_list["uri"],
                        "spotify_track_name": sp_track.name,
                        "found": False,
                        "karaoke": False,
                    }
                })

        # Once we have all the gm_trackids, add them
        if len(gm_track_ids) > 0:
            print "Creating in Google Music... ",
            playlist_id = g.create_playlist(sp_playlist.name)
            g.add_songs_to_playlist(playlist_id, gm_track_ids)
            print "Done"
        emit("portify", {"type": "playlist_ended",
                         "data": playlist_json})
    emit("portify", {"type": "all_done", "data": None})


sns = None


class GlobalNamespace(BaseNamespace):

    def initialize(self):
        self.logger = app.logger
        self.log("Socketio session started")

    def log(self, message):
        print message
        self.logger.info("[{0}] {1}".format(self.socket.sessid, message))

    def recv_connect(self):
        self.log("New connection")
        global sns
        sns = self

    def recv_disconnect(self):
        self.log("Client disconnected")


def emit(*args, **kwargs):
    if sns is not None:
        sns.emit(*args, **kwargs)


@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        print "Managing socket.io"
        socketio_manage(request.environ, {'/info': GlobalNamespace}, request)
    except:
        app.logger.error("Exception while handling socketio connection",
                         exc_info=True)
    return Response()


if __name__ == "__main__":
    app.run()
