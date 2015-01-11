import json
import threading
from django.conf import settings

from django.http import JsonResponse
from gmusicapi import Mobileclient
import spotify


class UserScope(object):

    def __init__(self):
        self.googleapi = Mobileclient()

        config = spotify.Config()
        config.load_application_key_file(settings.SPOTIFY_APPKEY)
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


def google_login(request):

    data = json.loads(request.body)

    email = data.get("email")
    password = data.get("password")

    user_scope.google_login(email, password)
    if not user_scope.google_loggedin():
        return JsonResponse(dict(
            status=400,
            message="login failed.",
        ))

    return JsonResponse(dict(
        status=200,
        message="login successful."
    ))


def spotify_login(request):

    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    user_scope.spotify_login(username, password)
    if not user_scope.spotify_loggedin():
        return JsonResponse(dict(
            status=400,
            message="login failed.",
        ))
    return JsonResponse(dict(
        status=200,
        message="login successful."
    ))


def transfer_start(request):

    lists = json.loads(request.body)

    if not user_scope.google_loggedin():
        return JsonResponse({"status": 401, "message": "Google: not logged in."})

    if not user_scope.spotify_loggedin():
        return JsonResponse({"status": 402, "message": "Spotify: not logged in."})

    if not lists:
        return JsonResponse({"status": 403, "message": "Please select at least one playlist."})

    transfer_playlists(lists)
    return JsonResponse({"status": 200, "message": "transfer will start."})


def spotify_playlists(request):

    container = user_scope.spotify_session.playlist_container
    playlists = container.load()

    ret_playlists = [{
        "name": "Starred Tracks",
        "uri": "spotify:user:%s:playlist:starred"
               % user_scope.spotify_session.remembered_user_name,
    }]

    for playlist in playlists:
        playlist.load()
        plist = {
            "name": playlist.name,
            "uri": playlist.link.uri,
        }
        ret_playlists.append(plist)

    return JsonResponse({"status": 200, "message": "ok", "data": ret_playlists})


def transfer_playlists(playlists):
    s = user_scope.spotify_session
    g = user_scope.googleapi
    for d_list in playlists:
        if ":starred" in d_list["uri"]:
            # TODO: Starred list
            continue
        sp_playlist = s.get_playlist(d_list["uri"])
        gm_track_ids = []

        print "Gathering tracks for playlist %s" % sp_playlist.name

        track_count = len(sp_playlist.tracks)
        for i, sp_track in enumerate(sp_playlist.tracks):
            sp_track.load()
            if sp_track.artists:
                sp_artist = sp_track.artists[0]
            else:
                sp_artist = None

            search_query = "%s - %s" % (sp_artist.name, sp_track.name)
            search_results = g.search_all_access(search_query, max_results=1)
            songs = search_results.get("song_hits")
            if songs:
                gm_track_id = songs[0]["track"]["nid"]
                gm_track_ids.append(gm_track_id)
                print "(%s/%s) Found '%s' in Google Music" % (i+1, track_count, search_query)
            else:
                print "(%s/%s) No match found for '%s'" % (i+1, track_count, search_query)

        # Once we have all the gm_trackids, add them
        if len(gm_track_ids) > 0:
            print "Creating in Google Music... ",
            playlist_id = g.create_playlist(sp_playlist.name)
            g.add_songs_to_playlist(playlist_id, gm_track_ids)
            print "Done"
