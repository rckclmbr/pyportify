#!/usr/bin/env python3

import asyncio
import pathlib
from pyportify.spotify import SpotifyClient, SpotifyQuery
from aiohttp import ClientSession


async def run():
    # https://developer.spotify.com/web-api/console/get-playlists/
    oauth_token = pathlib.Path(pathlib.Path.home(),
                               "secrets/spotify_access_token.txt")
    with ClientSession() as session:
        c = SpotifyClient(session, oauth_token)
        logged_in = await c.loggedin()
        if not logged_in:
            print("not logged in")
            return
        print("Logged in")

        # playlists = await c.fetch_spotify_playlists()
        # sp_playlist = playlists[0]
        sp_playlist_uri = 'spotify:user:22ujgyiomxbgggsb7mvnorh7q:playlist:3OVXBy5QDsx1jdSHrkAu1L'  # noqa
        pl = await c.fetch_playlist(sp_playlist_uri)
        tracks = pl['tracks']['items']
        for i, sp_track in enumerate(tracks):
            query = SpotifyQuery(i, sp_playlist_uri, sp_track, len(tracks))
            query.search_query()
        # print(sp_playlist["uri"])


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()


if __name__ == "__main__":
    main()
