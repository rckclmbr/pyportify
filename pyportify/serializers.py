class Track():
    artist = ""
    name = ""
    track_id = ""

    def __init__(self, artist, name, track_id=""):
        self.artist = artist
        self.name = name
        self.track_id = track_id

    @classmethod
    def from_spotify(cls, track):
        track_id = track.get("id")
        name = track.get("name")
        artist = ""
        if "artists" in track:
            artist = track["artists"][0]["name"]

        return cls(artist, name, track_id)

    @classmethod
    def from_gpm(cls, track):
        return cls(
            track.get("artist"),
            track.get("title"),
            track.get("storeId")
        )
