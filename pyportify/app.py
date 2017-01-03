import asyncio
from asyncio.locks import Semaphore
import json
import ssl
import logging

import aiohttp
import certifi
import os
import sys

from aiohttp import web, ClientSession
from aiohttp.web import json_response

from pyportify.middlwares import IndexMiddleware
from pyportify.spotify import SpotifyClient, SpotifyQuery
from pyportify.google import Mobileclient
import gmusicapi

IS_BUNDLED = getattr(sys, 'frozen', False)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

if IS_BUNDLED:
    STATIC_ROOT = os.path.dirname(sys.modules['pyportify'].__file__)
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

log = logging.getLogger(__name__)


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

    log.info('Logging into Google as %s', email)

    with ClientSession() as session:
        g = Mobileclient(session)
        token = yield from g.login(email, password)
        if not token:
            return json_response(dict(
                status=400,
                message="login failed.",
            ))
        user_scope.google_token = token

    log.info('Caching all playlists from Google')
    yield from g.cache_playlists()

    return json_response(dict(status=200, message="login successful."))


@asyncio.coroutine
def spotify_login(request):
    data = yield from request.json()

    log.info('Logging into Spotify')

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

    return json_response(dict(status=200, message="login successful."))


@asyncio.coroutine
def transfer_start(request):
    lists = yield from request.json()

    log.info('Starting transfer of %d playlists', len(lists))

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
    log.info('Fetching Spotify playlists')

    with ClientSession() as session:
        c = SpotifyClient(session, user_scope.spotify_token)
        ret_playlists = yield from c.fetch_spotify_playlists()
        return json_response({"status": 200, "message": "ok", "data": ret_playlists})


@asyncio.coroutine
def transfer_playlist(request, s, g, sp_playlist):
    log.info("[%s] Fetching tracks for playlist", sp_playlist['name'])
    sp_playlist_tracks = yield from s.fetch_playlist_tracks(sp_playlist['uri'])
    track_count = len(sp_playlist_tracks)

    playlist_json = {
        "playlist": {
            "uri": sp_playlist['uri'],
            "name": sp_playlist['name'],
        },
        "name": sp_playlist['name'],
    }

    yield from emit_playlist_length(request, track_count)
    yield from emit_playlist_started(request, playlist_json)

    if not sp_playlist_tracks:
        yield from emit_playlist_ended(request, playlist_json)
        return

    log.info("[%s] Mapping tracks for playlist (%d)", sp_playlist['name'], track_count)

    tasks = []
    for i, sp_track in enumerate(sp_playlist_tracks):
        query = SpotifyQuery(i, sp_playlist['uri'], sp_track, track_count)
        fut = search_gm_track(request, g, query)
        tasks.append(fut)
    gm_track_map = yield from asyncio.gather(*tasks)
    gm_track_ids = set((t for t in gm_track_map if t))

    log.info("[%s] Mapped tracks for playlist (%d out of %d)",
             sp_playlist['name'], len(gm_track_ids), track_count)

    missing_track_ids = [
        sp_playlist_tracks[x].get('name', sp_playlist_tracks[x].get('id', sp_playlist_tracks[x]))
        for x, val in enumerate(gm_track_map)
        if val is None
    ]
    if missing_track_ids:
        log.error("[%s] Missing %d tracks on Google, these will NOT be added for obvious reasons: %s",
                  sp_playlist['name'], len(missing_track_ids), missing_track_ids)

    split_count = int(len(gm_track_map) / 1000) + 1
    if split_count > 1:
        log.warning('[%s] There is a 1000 track limit per playlist on Google, splitting into %d playlists',
                    sp_playlist['name'], split_count)

    for split_id in range(1, split_count + 1):
        playlist_name = sp_playlist['name']
        if split_count > 1:
            playlist_name += ' %d' % split_id

        try:
            gpl = yield from g.get_cached_playlist(name=playlist_name)
            playlist_id = gpl['id']
            log.info("[%s] Playlist already exists on Google id=%s", playlist_name, playlist_id)
        except KeyError:
            playlist_id = yield from g.create_playlist(playlist_name)
            log.info("[%s] Created playlist on Google id=%s", playlist_name, playlist_id)

        log.info(
            "[%s] Ensuring tracks (%d out of %d) are in playlist on Google.", playlist_name,
            len(gm_track_ids), track_count
        )
        added_track_ids = yield from g.ensure_songs_in_playlist(playlist_id, gm_track_ids)
        log.info('[%s] Added %d tracks to Google', playlist_name, len(added_track_ids))

    log.info("[%s] Done syncing playlist to Google.", sp_playlist['name'])
    yield from emit_playlist_ended(request, playlist_json)


@asyncio.coroutine
def transfer_playlists(request, s, g, playlists):
    log.info('Transferring %s playlists', len(playlists))
    tasks = [transfer_playlist(request, s, g, pl) for pl in playlists]
    done = yield from asyncio.gather(*tasks)
    yield from emit_all_done(request)


@asyncio.coroutine
def emit(request, event, data):
    if request is None:
        # log.info("Not emitting {0}".format(event))
        return

    for ws in request.app['sockets']:
        ws.send_str(json.dumps({'eventName': event, 'eventData': data}))


@asyncio.coroutine
def emit_added_event(request, found, sp_playlist_uri, search_query):
    yield from emit(
        request, "gmusic", {
            "type": "added" if found else "not_added",
            "data": {
                "spotify_track_uri": sp_playlist_uri,
                "spotify_track_name": search_query,
                "found": found,
                "karaoke": False,
            }
        }
    )


@asyncio.coroutine
def emit_playlist_length(request, track_count):
    yield from emit(request, "portify", {"type": "playlist_length", "data": {"length": track_count}})


@asyncio.coroutine
def emit_playlist_started(request, playlist_json):
    yield from emit(request, "portify", {"type": "playlist_started", "data": playlist_json})


@asyncio.coroutine
def emit_playlist_ended(request, playlist_json):
    yield from emit(request, "portify", {"type": "playlist_ended", "data": playlist_json})


@asyncio.coroutine
def emit_all_done(request):
    yield from emit(request, "portify", {"type": "all_done", "data": None})


@asyncio.coroutine
def search_gm_track(request, g, sp_query):
    with (yield from semaphore):
        search_query = sp_query.search_query()

        track = yield from g.find_best_track(search_query)
        if track:
            gm_log_found(sp_query)
            yield from emit_added_event(request, True, sp_query.playlist_uri, search_query)
            return track['nid']

        gm_log_not_found(sp_query)
        yield from emit_added_event(request, False, sp_query.playlist_uri, search_query)
        return None


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


def gm_log_found(sp_query):
    log.info("({0}/{1}) Found '{2}' in Google".format(sp_query.i + 1, sp_query.track_count, sp_query.search_query()))


def gm_log_not_found(sp_query):
    log.info(
        "({0}/{1}) No match found for '{2}' in Google".
        format(sp_query.i + 1, sp_query.track_count, sp_query.search_query())
    )


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

    log.info("Listening on http://0.0.0.0:3132")
    log.info("Please open your browser window to http://localhost:3132")

    return handler1
