import json
import requests

from config import genres


def get_top_100_playables(genre):
    r = requests.get("https://www.beatport.com/{}/{}/top-100".format("genre" if genres[genre] else "", genres[genre]))
    blob_start = r.text.find("window.Playables") + 19
    blob_end = r.text.find("};", blob_start) + 1
    blob = r.text[blob_start:blob_end].replace("\n", "")
    return json.loads(blob)


def parse_tracks(tracks_json):
    tracks = list()
    for track in tracks_json["tracks"]:
        tracks.append(
            {
                "title": track["title"],
                "name": track["name"],
                "mix": track["mix"],
                "artists": [artist["name"] for artist in track["artists"]],
                "remixers": [remixer["name"] for remixer in track["remixers"]],
                "release": track["release"]["name"],
                "label": track["label"]["name"],
                "published_date": track["date"]["published"],
                "released_date": track["date"]["released"],
                "duration": track["duration"]["minutes"],
                "duration_ms": track["duration"]["milliseconds"],
                "genres": [genre["name"] for genre in track["genres"]],
                "bpm": track["bpm"],
                "key": track["key"]
            }
        )
    return tracks


def get_top_100_tracks(genre):
    print("[+] Fetching Top 100 {} Tracks".format(genre))
    raw_tracks_dict = get_top_100_playables(genre)
    return parse_tracks(raw_tracks_dict)
