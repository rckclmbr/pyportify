#!/usr/bin/env python3

import asyncio
import ssl
import pathlib
import sys

import aiohttp
from aiohttp import ClientSession
import certifi


from pyportify import app
from pyportify.google import Mobileclient
from pyportify.spotify import SpotifyClient
from pyportify.util import uprint

try:
    input = raw_input
except NameError:
    pass

OAUTH_URL = \
    "https://developer.spotify.com/web-api/console/get-playlist-tracks/"

google_email = "rckclmbr@gmail.com"
google_pass = pathlib.Path(
    pathlib.Path.home(),
    "secrets/pyportify_google_pass.txt").read_text()

# https://developer.spotify.com/web-api/console/get-playlists/
spotify_token = pathlib.Path(
    pathlib.Path.home(),
    "secrets/pyportify_spotify_token.txt").read_text()


async def test_percent_search(g):
    ret = await g.search_all_access("Hello % there")
    print(ret)


async def test_playlist(s, g):
    # uri = "spotify:user:lunsku:playlist:0OG0sShb7v1eU5brRfKDpv"
    uri = "spotify:user:22ujgyiomxbgggsb7mvnorh7q:playlist:3OVXBy5QDsx1jdSHrkAu1L"  # noqa
    await app.transfer_playlists(None, s, g, [uri])


async def start():

    sslcontext = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl_context=sslcontext)

    with ClientSession(connector=conn) as session:

        g = Mobileclient(session)
        logged_in = await g.login(google_email, google_pass)
        if not logged_in:
            uprint("Invalid Google username/password")
            sys.exit(1)

        s = SpotifyClient(session, spotify_token)

        logged_in = await s.loggedin()
        if not logged_in:
            uprint("Invalid Spotify token")
            sys.exit(1)

        await test_percent_search(g)
        await test_playlist(s, g)
        return

        # di = await g.fetch_playlists()
        # import pprint
        # pprint.pprint(di['data']['items'])
        #
        # # playlist_id = await g.create_playlist("Test Playlist")
        # playlist_id = "2c02eca1-429e-4ce0-a4a8-819415cdee3a"
        # await g.add_songs_to_playlist(
        #     playlist_id,
        #     ['Twqujxontbfftlzi7hextragxyu'],
        #     # ['ba3a473e-6309-3814-8c05-b8b6619f38f3'],
        # )
        playlists = await s.fetch_spotify_playlists()
        playlists = [l['uri'] for l in playlists]
        await app.transfer_playlists(None, s, g, playlists)


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start())
    finally:
        loop.close()


if __name__ == '__main__':
    main()
