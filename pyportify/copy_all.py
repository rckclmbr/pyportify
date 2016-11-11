#!/usr/bin/env python3

import asyncio
import ssl
from getpass import getpass
import sys
import os
import yaml
import gmusicapi
import pickle

import aiohttp
from aiohttp import ClientSession
import certifi

from pyportify import app
from pyportify.google import Mobileclient
from pyportify.spotify import SpotifyClient
import logging
log = logging.getLogger(__name__)

try:
    input = raw_input
except NameError:
    pass

OAUTH_URL = \
    "https://developer.spotify.com/web-api/console/get-playlist-tracks/"

CONFIG_FILE = 'pyportify.yml'


@asyncio.coroutine
def start():
    sslcontext = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl_context=sslcontext)

    with ClientSession(connector=conn) as session:
        conf = dict(
            google_email=None,
            google_pass=None,
            spotify_token=None,
        )

        try:
            with open(CONFIG_FILE, 'r') as f:
                conf.update(yaml.load(f))
        except Exception as exc:
            if not os.path.exists(CONFIG_FILE):
                log.info('Could not load from config file {}: {}'.format(CONFIG_FILE, exc))

        if not conf['google_email']:
            conf['google_email'] = input("Enter Google email address: ")
        if not conf['google_pass']:
            conf['google_pass'] = getpass("Enter Google password: ")

        g = Mobileclient(session)

        logged_in = yield from g.login(conf['google_email'], conf['google_pass'])
        if not logged_in:
            log.info("Invalid Google username/password")
            sys.exit(1)

        if not conf['spotify_token']:
            log.info("Go to {0} and get an oauth token".format(OAUTH_URL))
            conf['spotify_token'] = input("Enter Spotify oauth token: ")

        s = SpotifyClient(session, conf['spotify_token'])

        logged_in = yield from s.loggedin()
        if not logged_in:
            log.info("Invalid Spotify token")
            sys.exit(1)

        log.info('Caching all playlists from Google')
        if os.path.exists('google_playlists.pickle'):
            with open('google_playlists.pickle', 'rb') as f:
                g._playlists = pickle.load(f)
        else:
            yield from g.cache_playlists()
            with open('google_playlists.pickle', 'wb') as f:
                pickle.dump(g._playlists, f)

        log.info('Fetching Spotify playlists')
        playlists = yield from s.fetch_spotify_playlists()

        log.info('Starting sync')
        done = yield from app.transfer_playlists(None, s, g, playlists)
        log.debug('done=%s', done)

        log.info('Success!')


def main():
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    try:
        loop.run_until_complete(start())
    finally:
        loop.close()

if __name__ == '__main__':
    main()
