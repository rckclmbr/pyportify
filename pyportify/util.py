import itertools
import sys

from difflib import SequenceMatcher as SM


def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        def f(obj):
            return str(obj) \
                .encode(enc, errors='backslashreplace') \
                .decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)


def grouper(iterable, n):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def get_similarity(s1, s2):
    """
    Return similarity of both strings as a float between 0 and 1
    """
    return SM(None, s1, s2).ratio()


def find_closest_match(target_track, tracks):
    """
    Return closest match to target track
    """
    track = None
    # Get a list of (track, artist match ratio, name match ratio)
    tracks_with_match_ratio = [(
        track,
        get_similarity(target_track.artist, track.artist),
        get_similarity(target_track.name, track.name),
    ) for track in tracks]
    # Sort by artist then by title
    sorted_tracks = sorted(
        tracks_with_match_ratio,
        key=lambda t: (t[1], t[2]),
        reverse=True  # Descending, highest match ratio first
    )
    if sorted_tracks:
        track = sorted_tracks[0][0]  # Closest match to query
    return track
