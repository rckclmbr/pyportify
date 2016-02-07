
import asyncio
import json
import ssl

import aiohttp
import certifi
import os
import sys

from aiohttp import web, ClientSession
from aiohttp.web import json_response
from pyportify import dispatcher

from pyportify.spotify import SpotifyClient, get_queries
from pyportify.google import Mobileclient
from pyportify.util import uprint

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, "static")


class UserScope(object):

    def __init__(self):
        self.google_token = None
        self.spotify_token = None


user_scope = UserScope()


@asyncio.coroutine
def google_login(request):

    data = yield from request.json()

    email = data.get("email")
    password = data.get("password")

    with ClientSession() as session:
        g = Mobileclient(session)
        token = yield from g.login(email, password)
        if not token:
            return json_response(dict(
                status=400,
                message="login failed.",
            ))
        user_scope.google_token = token
    return json_response(dict(
        status=200,
        message="login successful."
    ))


@asyncio.coroutine
def spotify_login(request):

    data = yield from request.json()

    oauth_token = data.get("oauthToken")
    with ClientSession() as session:
        c = SpotifyClient(session, oauth_token)
        logged_in = yield from c.loggedin()
        if not logged_in:
            return json_response(dict(
                status=400,
                message="login failed.",
            ))
        user_scope.spotify_token = oauth_token

    return json_response(dict(
        status=200,
        message="login successful."
    ))


@asyncio.coroutine
def transfer_start(request):

    lists = yield from request.json()

    if not user_scope.google_token:
        return json_response({
            "status": 401,
            "message": "Google: not logged in.",
        })

    if not user_scope.spotify_token:
        return json_response({
            "status": 402,
            "message": "Spotify: not logged in.",
        })

    if not lists:
        return json_response({
            "status": 403,
            "message": "Please select at least one playlist.",
        })

    sslcontext = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl_context=sslcontext)

    with ClientSession(connector=conn) as session:
        g = Mobileclient(session, user_scope.google_token)
        s = SpotifyClient(session, user_scope.spotify_token)

        yield from transfer_playlists(request, session, s, g, lists)
        return json_response({
            "status": 200,
            "message": "transfer will start.",
        })


@asyncio.coroutine
def spotify_playlists(request):
    with ClientSession() as session:
        c = SpotifyClient(session, user_scope.spotify_token)
        ret_playlists = yield from c.fetch_spotify_playlists()
        return json_response({
            "status": 200,
            "message": "ok",
            "data": ret_playlists
        })


@asyncio.coroutine
def transfer_playlists(request, session, s, g, playlists):
    for d_list in playlists:
        sp_playlist = yield from s.fetch_playlist(d_list["uri"])
        sp_playlist_tracks = yield from s.fetch_playlist_tracks(d_list["uri"])

        track_count = len(sp_playlist_tracks)
        uprint(
            "Gathering tracks for playlist %s (%s)" %
            (sp_playlist['name'], track_count)
        )
        playlist_json = {
            "playlist": {
                "uri": d_list["uri"],
                "name": sp_playlist['name'],
            },
            "name": sp_playlist['name'],
        }
        yield from emit(
            request,
            "portify",
            {"type": "playlist_length", "data": {"length": track_count}}
        )
        yield from emit(
            request,
            "portify",
            {"type": "playlist_started", "data": playlist_json}
        )

        gm_track_ids = [None] * len(sp_playlist_tracks)

        @asyncio.coroutine
        def search_gm_track(args):
            i, spotify_uri, search_query = args
            track = yield from g.find_best_track(search_query)
            if track:
                gm_track_id = track["nid"]
                gm_track_ids[i] = gm_track_id
                uprint(
                    "({0}/{1}) Found '{2}' in Google Music".format(
                        i+1, track_count, search_query
                    )
                )
                yield from emit(request, "gmusic", {
                    "type": "added",
                    "data": {
                        "spotify_track_uri": spotify_uri,
                        "spotify_track_name": search_query,
                        "found": True,
                        "karaoke": False,
                    }
                })
            else:
                uprint(
                    "({0}/{1}) No match found for '{2}'"
                    .format(i+1, track_count, search_query)
                )
                yield from emit(request, "gmusic", {
                    "type": "not_added",
                    "data": {
                        "spotify_track_uri": spotify_uri,
                        "spotify_track_name": search_query,
                        "found": False,
                        "karaoke": False,
                    }
                })
            return i

        queries = get_queries(d_list['uri'], sp_playlist_tracks)
        tasks = [search_gm_track(query) for query in queries]
        if tasks:
            yield from asyncio.wait(tasks)
        gm_track_ids = [i for i in gm_track_ids if i is not None]

        # Once we have all the gm_trackids, add them
        if len(gm_track_ids) > 0:
            uprint("Creating in Google Music... ", end='')
            sys.stdout.flush()
            playlist_id = yield from g.create_playlist(sp_playlist['name'])
            yield from g.add_songs_to_playlist(playlist_id, gm_track_ids)
            uprint("Done")
        yield from emit(
            request,
            "portify",
            {"type": "playlist_ended", "data": playlist_json}
        )
    yield from emit(request, "portify", {"type": "all_done", "data": None})


@asyncio.coroutine
def emit(request, event, data):
    if request is None:
        uprint("Not emitting {0}".format(event))
        return

    for ws in request.app['sockets']:
        ws.send_str(json.dumps({'eventName': event, 'eventData': data}))


@asyncio.coroutine
def wshandler(request):
    resp = web.WebSocketResponse()
    ok, protocol = resp.can_start(request)
    if not ok:
        raise Exception("Couldn't start websocket")

    yield from resp.prepare(request)
    request.app['sockets'].append(resp)

    while True:
        msg = yield from resp.receive()

        if msg.tp == web.MsgType.text:
            pass
        else:
            break

    request.app['sockets'].remove(resp)
    return resp


@asyncio.coroutine
def setup(loop):
    app1 = web.Application(loop=loop)
    app1['sockets'] = []
    app1.router.add_route('POST', '/google/login', google_login)
    app1.router.add_route('POST', '/spotify/login', spotify_login)
    app1.router.add_route('POST', '/portify/transfer/start', transfer_start)
    app1.router.add_route('GET', '/spotify/playlists', spotify_playlists)
    app1.router.add_route('GET', '/ws/', wshandler)
    app1.router.add_route(
        'GET',
        r'/{url_path:.*}',
        dispatcher.static_factory('/', STATIC_ROOT),
    )

    handler1 = app1.make_handler()

    yield from loop.create_server(handler1, '0.0.0.0', 3132)

    uprint("Listening on http://0.0.0.0:3132")
    uprint("Please open your browser window to http://localhost:3132")

    return handler1
