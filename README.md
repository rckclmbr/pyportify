Pyportify
=========

[![Build Status](https://travis-ci.org/rckclmbr/pyportify.svg?branch=master)](https://travis-ci.org/rckclmbr/pyportify)

A port of [portify](https://github.com/mauimauer/portify) to python.

But it actually works.

Transfers your Spotify Premium playlists to Google Music: All Access

By using Pyportify you may violate both Spotify's and Google's Terms of Service. You agree that
you are using Pyportify on your own risk. The author does not accept liability (as far as permitted by law) for any loss arising from any use of this tool.
If you choose not to agree to these terms, then you may not use this tool.

If you are unable to sign in to your Google account, try using Google App Passwords: https://security.google.com/settings/security/apppasswords

Download
--------

Windows:

https://github.com/rckclmbr/pyportify/releases/download/v0.4.1/pyportify.zip

OSX:

https://github.com/rckclmbr/pyportify/releases/download/v0.4.1/pyportify.dmg

Install from pypi
-----------------

OS X:

```bash
$ brew install python3
$ pip3 install pyportify
```

If you are having issues with ```pyportify: command not found```, please make sure you have set your ```PATH``` correctly.


If you are having permission error messages with pip on installation, uninstall pyportify then reinstall using the commands below:

```bash
$ pip3 uninstall pyportify
$ sudo -H pip3 install pyportify
```

Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip
sudo pip3 install pyportify
```

Fedora

```bash
sudo yum check-update
sudo pip install pyportify
```

Running
-------

```
$ pyportify
# Now open a browser to http://localhost:3132
```

EZ

Alternatively, you can copy all playlists easily using the ```pyportify-copyall``` command:

```bash
$ pyportify-copyall
Enter Google email address: example@gmail.com
Enter Google password:
Go to https://developer.spotify.com/web-api/console/get-playlist-tracks/ and get an oauth token
Enter Spotify oauth token: <access token>
(transfer music)
...
```

Or, use Docker:

```
$ docker run -t -i --rm -p 3132:3132 rckclmbr/pyportify

or

$ docker run -t -i --rm rckclmbr/pyportify /usr/local/bin/pyportify-copyall
```

License
-------

Licensed under the terms of the Apache 2.0 License
All Trademarks are the property of their respective owners.
