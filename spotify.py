import sys
import json
import socket
import spotipy
import asyncio
import webbrowser
from time import time
from spotipy import oauth2

from config import *


def listen_for_callback_code():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", int(redirect_uri.split(":")[-1])))
    s.listen(1)
    while True:
        connection, address = s.accept()
        buf = str(connection.recv(1024))
        if len(buf) > 0:
            break
    start_code = buf.find("?code=") + 6
    end_code = buf.find(" ", start_code)
    if "&" in buf[start_code:end_code]:
        end_code = buf.find("&")
    return buf[start_code:end_code]


async def get_spotify_auth_code():
    auth_url = sp_oauth.get_authorize_url()
    webbrowser.open(auth_url)


async def async_get_auth_code():
    task = asyncio.create_task(get_spotify_auth_code())
    await task
    return listen_for_callback_code()


def do_spotify_oauth():
    try:
        with open("token.json", "r") as fh:
            token = fh.read()
        token = json.loads(token)
    except:
        token = None
    if token:
        if int(time()) > token["expires_at"]:
            token = sp_oauth.refresh_access_token(token["refresh_token"])
    else:
        authorization_code = asyncio.run(async_get_auth_code())
        print(authorization_code)
        if not authorization_code:
            print(
                "\n[!] Unable to authenticate to Spotify.  Couldn't get authorization code"
            )
            sys.exit(-1)
        token = sp_oauth.get_access_token(authorization_code)
    if not token:
        print("\n[!] Unable to authenticate to Spotify.  Couldn't get access token.")
        sys.exit(-1)
    try:
        with open("token.json", "w+") as fh:
            fh.write(json.dumps(token))
    except:
        print("\n[!] Unable to to write token object to disk.  This is non-fatal.")
    return token


def get_all_playlists():
    playlists_pager = spotify.user_playlists(user_id)
    playlists = playlists_pager["items"]
    while playlists_pager["next"]:
        playlists_pager = spotify.next(playlists_pager)
        playlists.extend(playlists_pager["items"])
    return playlists


def create_playlist(playlist_name):
    playlist = spotify.user_playlist_create(user_id, playlist_name)
    return playlist["id"]


def get_playlist_id(playlist_name):
    playlists = get_all_playlists()
    for playlist in playlists:
        if playlist["name"] == playlist_name:
            return playlist["id"]
    return None


def do_durations_match(source_track_duration, found_track_duration):
    if source_track_duration == found_track_duration:
        print("\t\t\t\t[+] Durations match")
        return True
    else:
        print("\t\t\t\t[!] Durations do not match")
        return False


def most_popular_track(tracks):
    # Popularity does not always yield the correct result
    high_score = 0
    winner = None
    for track in tracks:
        if track["popularity"] > high_score:
            winner = track["id"]
            high_score = track["popularity"]
    return winner


def best_of_multiple_matches(source_track, found_tracks):
    counter = 1
    duration_matches = [
        0,
    ]
    for track in found_tracks:
        print("\t\t\t[+] Match {}: {}".format(counter, track["id"]))
        if do_durations_match(source_track["duration_ms"], track["duration_ms"]):
            duration_matches[0] += 1
            duration_matches.append(track)
        counter += 1
    if duration_matches[0] == 1:
        best_track = duration_matches.pop()["id"]
        print(
            "\t\t\t[+] Only one exact match with matching duration, going with that one: {}".format(
                best_track
            )
        )
        return best_track
    # TODO: Popularity does not always yield the correct result
    best_track = most_popular_track(found_tracks)
    print(
        "\t\t\t[+] Multiple exact matches with matching durations, going with the most popular one: {}".format(
            best_track
        )
    )
    return best_track


def search_for_track(track):
    try:
        # TODO: This is repetitive, can probably refactor but works for now
        print(
            "\n[+] Searching for track: {}{}by {} on {}".format(
                track["name"],
                " " if not track["mix"] else " ({}) ".format(track["mix"]),
                ", ".join(track["artists"]),
                track["release"],
            )
        )
        # Search with Title, Mix, Artists, and Release / Album
        query = "{}{}{} {}".format(
            track["name"],
            " " if not track["mix"] else " {} ".format(track["mix"]),
            " ".join(track["artists"]),
            track["release"],
        )
        print("\t[+] Search Query: {}".format(query))

        search_results = spotify.search(query)
        if len(search_results["tracks"]["items"]) == 1:
            track_id = search_results["tracks"]["items"][0]["id"]
            print(
                "\t\t[+] Found an exact match on name, mix, artists, and release: {}".format(
                    track_id
                )
            )
            do_durations_match(
                track["duration_ms"],
                search_results["tracks"]["items"][0]["duration_ms"],
            )
            return track_id

        if len(search_results["tracks"]["items"]) > 1:
            print(
                "\t\t[+] Found multiple exact matches ({}) on name, mix, artists, and release.".format(
                    len(search_results["tracks"]["items"])
                )
            )
            return best_of_multiple_matches(track, search_results["tracks"]["items"])

        # Not enough results, search w/o release
        print(
            "\t\t[+] No exact matches on name, mix, artists, and release.  Trying without release."
        )
        # Search with Title, Mix, and Artists
        query = "{}{}{}".format(
            track["name"],
            " " if not track["mix"] else " {} ".format(track["mix"]),
            " ".join(track["artists"]),
        )
        print("\t[+] Search Query: {}".format(query))
        search_results = spotify.search(query)
        if len(search_results["tracks"]["items"]) == 1:
            track_id = search_results["tracks"]["items"][0]["id"]
            print(
                "\t\t[+] Found an exact match on name, mix, and artists: {}".format(
                    track_id
                )
            )
            do_durations_match(
                track["duration_ms"],
                search_results["tracks"]["items"][0]["duration_ms"],
            )
            return track_id

        if len(search_results["tracks"]["items"]) > 1:
            print(
                "\t\t[+] Found multiple exact matches ({}) on name, mix, and artists.".format(
                    len(search_results["tracks"]["items"])
                )
            )
            return best_of_multiple_matches(track, search_results["tracks"]["items"])

        # Not enough results, search w/o mix, but with release
        print(
            "\t\t[+] No exact matches on name, mix, and artists.  Trying without mix, but with release."
        )
        query = "{} {} {}".format(
            track["name"], " ".join(track["artists"]), track["release"]
        )
        print("\t[+] Search Query: {}".format(query))
        search_results = spotify.search(query)
        if len(search_results["tracks"]["items"]) == 1:
            track_id = search_results["tracks"]["items"][0]["id"]
            print(
                "\t\t[+] Found an exact match on name, artists, and release: {}".format(
                    track_id
                )
            )
            do_durations_match(
                track["duration_ms"],
                search_results["tracks"]["items"][0]["duration_ms"],
            )
            return track_id

        if len(search_results["tracks"]["items"]) > 1:
            print(
                "\t\t[+] Found multiple exact matches ({}) on name, artists, and release.".format(
                    len(search_results["tracks"]["items"])
                )
            )
            return best_of_multiple_matches(track, search_results["tracks"]["items"])

        # Not enough results, search w/o mix or release
        print(
            "\t\t[+] No exact matches on name, artists, and release.  Trying with just name and artists."
        )
        query = "{} {}".format(track["name"], " ".join(track["artists"]))
        print("\t[+] Search Query: {}".format(query))
        search_results = spotify.search(query)
        if len(search_results["tracks"]["items"]) == 1:
            track_id = search_results["tracks"]["items"][0]["id"]
            print(
                "\t\t[+] Found an exact match on name and artists: {}".format(track_id)
            )
            do_durations_match(
                track["duration_ms"],
                search_results["tracks"]["items"][0]["duration_ms"],
            )
            return track_id

        if len(search_results["tracks"]["items"]) > 1:
            print(
                "\t\t[+] Found multiple exact matches ({}) on name and artists.".format(
                    len(search_results["tracks"]["items"])
                )
            )
            return best_of_multiple_matches(track, search_results["tracks"]["items"])

        print("\t\t[+] No exact matches on name and artists.")
        print("\t[!] Could not find this song on Spotify!")
        return None
    # TODO: better error handling
    except:
        print("Error when searching track")
        return None


def track_in_playlist(playlist_id, track_id):
    for track in get_all_tracks_in_playlist(playlist_id):
        if track["track"]["id"] == track_id:
            return True
    return False


def add_tracks_to_playlist(playlist_id, track_ids):
    if track_ids:
        spotify.user_playlist_add_tracks(user_id, playlist_id, track_ids)


def get_all_tracks_in_playlist(playlist_id):
    if playlist_id in playlist_track_cache:
        return playlist_track_cache[playlist_id]
    playlist_tracks_results = spotify.playlist(playlist_id, fields="tracks")
    playlist_tracks_pager = playlist_tracks_results["tracks"]
    playlist_tracks = playlist_tracks_pager["items"]
    while playlist_tracks_pager["next"]:
        playlist_tracks_pager = spotify.next(playlist_tracks_pager)
        playlist_tracks.extend(playlist_tracks_pager["items"])
    playlist_track_cache[playlist_id] = playlist_tracks
    return playlist_track_cache[playlist_id]


def clear_playlist(playlist_id):
    for track in get_all_tracks_in_playlist(playlist_id):
        spotify.user_playlist_remove_all_occurrences_of_tracks(
            user_id,
            playlist_id,
            [
                track["track"]["id"],
            ],
        )


def add_new_tracks_to_playlist(genre, tracks_dict):
    persistent_top_100_playlist_name = "Beatporter: {} - Top 100".format(genre)
    daily_top_10_playlist_name = "Beatporter: {} - Daily Top 10".format(genre)
    print(
        '[+] Identifying new tracks for playlist: "{}"'.format(
            persistent_top_100_playlist_name
        )
    )

    playlists = [
        {
            "name": persistent_top_100_playlist_name,
            "id": get_playlist_id(persistent_top_100_playlist_name),
        },
        {
            "name": daily_top_10_playlist_name,
            "id": get_playlist_id(daily_top_10_playlist_name),
        },
    ]

    for playlist in playlists:
        if not playlist["id"]:
            print(
                '\t[!] Playlist "{}" does not exist, creating it.'.format(
                    playlist["name"]
                )
            )
            playlist["id"] = create_playlist(playlist["name"])

    # Clear daily playlist
    clear_playlist(playlists[1]["id"])

    persistent_top_100_track_ids = list()
    daily_top_10_track_ids = list()
    track_count = 0
    for track in tracks_dict:
        track_id = search_for_track(track)
        if track_id and not track_in_playlist(playlists[0]["id"], track_id):
            persistent_top_100_track_ids.append(track_id)
        if track_id and track_count < 10:
            daily_top_10_track_ids.append(track_id)
        track_count += 1
    print(
        '\n[+] Adding {} new tracks to the playlist: "{}"'.format(
            len(persistent_top_100_track_ids), persistent_top_100_playlist_name
        )
    )
    add_tracks_to_playlist(playlists[0]["id"], persistent_top_100_track_ids)
    print(
        '\n[+] Adding {} new tracks to the playlist: "{}"'.format(
            len(daily_top_10_track_ids), daily_top_10_playlist_name
        )
    )
    add_tracks_to_playlist(playlists[1]["id"], daily_top_10_track_ids)


playlist_track_cache = dict()

# Get authenticated to Spotify on import
sp_oauth = oauth2.SpotifyOAuth(
    client_id, client_secret, redirect_uri, username=username, scope=scope
)
token_info = do_spotify_oauth()
spotify = spotipy.Spotify(auth=token_info["access_token"], requests_timeout=120)
