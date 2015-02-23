from getpass import getpass
import sys

from pyportify import views as app

try:
    input = raw_input
except NameError:
    pass


def main():

    google_email = input("Enter Google email address: ")
    google_pass = getpass("Enter Google password: ")

    app.user_scope.google_login(google_email, google_pass)
    if not app.user_scope.google_loggedin():
        print "Invalid Google username/password"
        sys.exit(1)

    spotify_user = input("Enter Spotify username: ")
    spotify_pass = getpass("Enter Spotify password: ")

    app.user_scope.spotify_login(spotify_user, spotify_pass)
    if not app.user_scope.spotify_loggedin():
        print "Invalid Spotify username/password"
        sys.exit(1)

    playlists = app.fetch_spotify_playlists()
    app.transfer_playlists(playlists)


if __name__ == '__main__':
    main()
