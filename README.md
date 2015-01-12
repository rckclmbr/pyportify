Pyportify
=========

A port of [portify](https://github.com/mauimauer/portify) to python.

But it actually works.

Transfers your Spotify playlists to Google Music: All Access

By using Portify you may violate both Spotify's and Google's Terms of Service. You agree that
you are using Portify on your own risk. The author does not accept liability (as far as permitted by law) for any loss arising from any use of this tool.
If you choose not to agree to these terms, then you may not use this tool.

You can read about portify here: [http://www.maui.at/2013/06/portify/](http://www.maui.at/2013/06/portify/)

Install
-------

OSX:

```bash
# Install libspotify
$ brew install homebrew/binary/libspotify
# Workaround on OSX (see https://pyspotify.mopidy.com/en/latest/installation/)
$ sudo ln -s /usr/local/opt/libspotify/lib/libspotify.12.1.51.dylib \
/usr/local/opt/libspotify/lib/libspotify
# Install pyportify
$ pip install pyportify
```

Ubuntu:

```bash
curl -s https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
sudo curl -s https://apt.mopidy.com/mopidy.list > /etc/apt/sources.list.d/mopidy.list
sudo apt-get update
sudo apt-get install -y python-pip python-dev libffi-dev libspotify-dev
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
Enter Spotify username: spotifyuser
Enter Spotify password:
(transfer music)
...
```

Or, use Docker:

```
$ docker run -t -i --rm -p 3132:3132 rckclmbr/pyportify

or

$ docker run -t -i --rm rckclmbr/pyportify /ve/bin/pyportify-copyall
```

License
-------

Licensed under the terms of the Apache 2.0 License
All Trademarks are the property of their respective owners.
