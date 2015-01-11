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

```bash
# Install libspotify (https://pyspotify.mopidy.com/en/latest/installation/)
$ brew install --pre libspotify
# Install pyportify
$ pip install pyportify
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
