
import asyncio
from asyncio.locks import Semaphore
import json
import ssl

import aiohttp
import certifi
import os
import sys

from aiohttp import web, ClientSession
from aiohttp.web import json_response

from pyportify.middlewares import IndexMiddleware
from pyportify.spotify import SpotifyClient, SpotifyQuery
from pyportify.google import Mobileclient
from pyportify.util import uprint, grouper

IS_BUNDLED = getattr(sys, 'frozen', False)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

if IS_BUNDLED:
    STATIC_ROOT = os.path.dirname(sys.modules['pyportify'].__file__)
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")


class UserScope(object):

    def __init__(self):
        self.google_token = None
        self.spotify_token = None


user_scope = UserScope()
semaphore = Semaphore(20)


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
    lists = [l['uri'] for l in lists]

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

        yield from transfer_playlists(request, s, g, lists)
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
def transfer_playlists(request, s, g, sp_playlist_uris):
    for sp_playlist_uri in sp_playlist_uris:
        sp_playlist = yield from s.fetch_playlist(sp_playlist_uri)
        sp_playlist_tracks = yield from s.fetch_playlist_tracks(
            sp_playlist_uri)

        track_count = len(sp_playlist_tracks)
        uprint(
            "Gathering tracks for playlist %s (%s)" %
            (sp_playlist['name'], track_count)
        )
        playlist_json = {
            "playlist": {
                "uri": sp_playlist_uri,
                "name": sp_playlist['name'],
            },
            "name": sp_playlist['name'],
        }

        yield from emit_playlist_length(request, track_count)
        yield from emit_playlist_started(request, playlist_json)

        if not sp_playlist_tracks:
            yield from emit_playlist_ended(request, playlist_json)
            return

        tasks = []
        for i, sp_track in enumerate(sp_playlist_tracks):
            query = SpotifyQuery(i, sp_playlist_uri, sp_track, track_count)
            future = search_gm_track(request, g, query)
            tasks.append(future)

        done = yield from asyncio.gather(*tasks)
        gm_track_ids = [i for i in done if i is not None]

        # Once we have all the gm_trackids, add them
        if len(gm_track_ids) > 0:
            uprint("Creating in Google Music... ", end='')
            sys.stdout.flush()
            for i, sub_gm_track_ids in enumerate(grouper(gm_track_ids, 1000)):
                name = sp_playlist['name']
                if i > 0:
                    name = "{} ({})".format(name, i+1)
                playlist_id = yield from g.create_playlist(name)
                yield from \
                    g.add_songs_to_playlist(playlist_id, sub_gm_track_ids)
            uprint("Done")

        yield from emit_playlist_ended(request, playlist_json)
    yield from emit_all_done(request)


@asyncio.coroutine
def emit(request, event, data):
    if request is None:
        # uprint("Not emitting {0}".format(event))
        return

    for ws in request.app['sockets']:
        ws.send_str(json.dumps({'eventName': event, 'eventData': data}))


@asyncio.coroutine
def emit_added_event(request, found, sp_playlist_uri, search_query):
    yield from emit(request, "gmusic", {
        "type": "added" if found else "not_added",
        "data": {
            "spotify_track_uri": sp_playlist_uri,
            "spotify_track_name": search_query,
            "found": found,
            "karaoke": False,
        }
    })


@asyncio.coroutine
def emit_playlist_length(request, track_count):
    yield from emit(request, "portify",
                    {"type": "playlist_length",
                     "data": {"length": track_count}})


@asyncio.coroutine
def emit_playlist_started(request, playlist_json):
    yield from emit(request, "portify",
                    {"type": "playlist_started", "data": playlist_json})


@asyncio.coroutine
def emit_playlist_ended(request, playlist_json):
    yield from emit(request, "portify",
                    {"type": "playlist_ended", "data": playlist_json})


@asyncio.coroutine
def emit_all_done(request):
    yield from emit(request, "portify", {"type": "all_done", "data": None})


@asyncio.coroutine
def search_gm_track(request, g, sp_query):
    with (yield from semaphore):
        track = None
        search_query = sp_query.search_query()
        if search_query:
            track = yield from g.find_best_track(search_query)
        if track:
            gm_log_found(sp_query)
            yield from emit_added_event(request, True,
                                        sp_query.playlist_uri, search_query)
            return track.get('storeId')

        gm_log_not_found(sp_query)
        yield from emit_added_event(request, False,
                                    sp_query.playlist_uri, search_query)
        return None


@asyncio.coroutine
def wshandler(request):
    resp = web.WebSocketResponse()
    ws_ready = resp.can_prepare(request)
    if not ws_ready.ok:
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


def gm_log_found(sp_query):
    uprint("({0}/{1}) Found '{2}' in Google Music".format(
           sp_query.i+1, sp_query.track_count, sp_query.search_query()))


def gm_log_not_found(sp_query):
    uprint("({0}/{1}) No match found for '{2}' in Google Music".format(
           sp_query.i+1, sp_query.track_count, sp_query.search_query()))


@asyncio.coroutine
def setup(loop):
    app1 = web.Application(loop=loop, middlewares=[IndexMiddleware()])
    app1['sockets'] = []
    app1.router.add_route('POST', '/google/login', google_login)
    app1.router.add_route('POST', '/spotify/login', spotify_login)
    app1.router.add_route('POST', '/portify/transfer/start', transfer_start)
    app1.router.add_route('GET', '/spotify/playlists', spotify_playlists)
    app1.router.add_route('GET', '/ws/', wshandler)
    app1.router.add_static('/', STATIC_ROOT)

    handler1 = app1.make_handler()

    yield from loop.create_server(handler1, '0.0.0.0', 3132)

    uprint("Listening on http://0.0.0.0:3132")
    uprint("Please open your browser window to http://localhost:3132")

    return handler1
