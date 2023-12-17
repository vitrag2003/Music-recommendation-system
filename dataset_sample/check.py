"""
    checks to make sure that the challenge_set is internally consistent

    usage: python check.py challenge_set.json
"""

import sys
import json

stats = {
    "tests": 0,
    "errors": 0,
}

required_playlist_fields = [
    "num_holdouts",
    "pid",
    "num_tracks",
    "tracks",
    "num_samples",
]
optional_playlist_fields = ["name"] + required_playlist_fields

track_fields = set(
    [
        "pos",
        "artist_name",
        "artist_uri",
        "track_uri",
        "track_name",
        "album_uri",
        "album_name",
        "duration_ms",
    ]
)


def check_challenge_set(path):
    with open(path) as f:
        js = f.read()
        challenge_set = json.loads(js)

        tassert(challenge_set["version"] == "v1", "proper version")
        tassert(len(challenge_set["playlists"]) == 10000, "proper number of playlists")

        known_ids = set()
        unique_tracks = set()
        unique_albums = set()
        unique_artists = set()
        total_tracks = 0
        for playlist in challenge_set["playlists"]:
            ntracks = playlist["num_samples"] + playlist["num_holdouts"]
            tassert(playlist["pid"] not in known_ids, "unique pid")
            tassert(ntracks == playlist["num_tracks"], "consistent num_tracks")
            tassert(
                playlist["num_samples"] == len(playlist["tracks"]), "consistent num_samples"
            )
            known_ids.add(playlist["pid"])

            for field, val in list(playlist.items()):
                tassert(field in optional_playlist_fields, "valid playlist field")

            for f in required_playlist_fields:
                tassert(f in list(playlist.keys()), "missing required play list field " + f)

            for track in playlist["tracks"]:
                for field, val in list(track.items()):
                    tassert(field in track_fields, "valid track field")
                for f in track_fields:
                    tassert(f in list(track.keys()), "missing required track field " + f)

                unique_tracks.add(track["track_uri"])
                unique_albums.add(track["album_uri"])
                unique_artists.add(track["artist_uri"])
                total_tracks += 1

        tassert(len(known_ids) == 10000, "proper number of unqiue IDs")

        print()
        print("stats:")
        for k, v in list(stats.items()):
            print("%s: %d" % (k, v))
        print()

        print("total playlists:", len(challenge_set["playlists"]))
        print("total tracks:   ", total_tracks)
        print("unique tracks:  ", len(unique_tracks))
        print("unique albums:  ", len(unique_albums))
        print("unique artists: ", len(unique_artists))
        print()

        if stats["errors"] == 0:
            print("challenge_set.json is OK")
        else:
            print("challenge_set.json has errors")


def tassert(cond, text):
    stats["tests"] += 1
    if not cond:
        stats["errors"] += 1
        print("error:" + text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check,py challenge_set.json")
    else:
        check_challenge_set(sys.argv[1])
