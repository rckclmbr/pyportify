#!/usr/bin/env python3

import asyncio
import ssl
from getpass import getpass
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


@asyncio.coroutine
def start():

    sslcontext = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl_context=sslcontext)

    with ClientSession(connector=conn) as session:

        google_email = input("Enter Google email address: ")
        google_pass = getpass("Enter Google password: ")

        g = Mobileclient(session)

        logged_in = yield from g.login(google_email, google_pass)
        if not logged_in:
            uprint("Invalid Google username/password")
            sys.exit(1)

        uprint("Go to {0} and get an oauth token".format(OAUTH_URL))
        spotify_token = input("Enter Spotify oauth token: ")

        s = SpotifyClient(session, spotify_token)

        logged_in = yield from s.loggedin()
        if not logged_in:
            uprint("Invalid Spotify token")
            sys.exit(1)

        playlists = yield from s.fetch_spotify_playlists()
        yield from app.transfer_playlists(None, s, g, playlists)


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start())
    finally:
        loop.close()

if __name__ == '__main__':
    main()
