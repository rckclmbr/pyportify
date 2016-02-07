#!/usr/bin/env python3

import asyncio
from getpass import getpass
import sys

from aiohttp import ClientSession

from pyportify import app
from pyportify.google import Mobileclient
from pyportify.spotify import SpotifyClient

try:
    input = raw_input
except NameError:
    pass

OAUTH_URL = \
    "https://developer.spotify.com/web-api/console/get-playlist-tracks/"


@asyncio.coroutine
def main():

    with ClientSession() as session:

        google_email = input("Enter Google email address: ")
        google_pass = getpass("Enter Google password: ")

        g = Mobileclient(session)

        logged_in = yield from g.login(google_email, google_pass)
        if not logged_in:
            print("Invalid Google username/password")
            sys.exit(1)

        print("Go to {0} and get an oauth token".format(OAUTH_URL))
        spotify_token = input("Enter Spotify oauth token: ")

        s = SpotifyClient(session, spotify_token)

        logged_in = yield from s.loggedin()
        if not logged_in:
            print("Invalid Spotify token")
            sys.exit(1)

        playlists = yield from s.fetch_playlists()
        yield from app.transfer_playlists(None, session, s, g, playlists)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
