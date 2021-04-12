import json
import requests
from bs4 import BeautifulSoup

from config import genres


def get_chart_genres():
    available_genres = dict()
    r = requests.get("https://www.beatport.com/charts")
    soup = BeautifulSoup(r.text)
    genre_list_items = soup.find("div", {"class": "bucket genre-list"}).find("ul", {"class": "bucket-items"}).find_all("li")
    for genre in genre_list_items:
        available_genres[genre.find("a").text] = genre.find("a").get("href")
    return available_genres


def get_genres():
    available_genres = {"All Genres": ""}
    r = requests.get("https://www.beatport.com/")
    soup = BeautifulSoup(r.text, "html.parser")
    genre_links = soup.find("li", {"class": "genre-parent head-parent"}).find_all("a")
    for genre in genre_links:
        available_genres[genre.text] = genre.get("href").strip("/genre")
    return available_genres


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
