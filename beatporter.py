import sys
import json
import spotify
import beatport
import argparse
from datetime import datetime


def dump_tracks(tracks):
    i = 1
    for track in tracks:
        print(
            "{}: {} ({}) - {} ({})".format(
                i,
                track["name"],
                track["mix"],
                ", ".join(track["artists"]),
                track["duration"],
            )
        )
        i += 1


if __name__ == "__main__":
    start_time = datetime.now()

    parser = argparse.ArgumentParser(description="Beatporter")
    parser.add_argument("--genres", action="store_true")
    args = parser.parse_args()

    if args.genres:
        print(json.dumps(beatport.get_genres(), indent=4))
        sys.exit()

    print("[!] Starting @ {}\n".format(start_time))
    top_100_charts = dict()
    for genre, genre_bp_url_code in beatport.genres.items():
        top_100_charts[genre] = beatport.get_top_100_tracks(genre)

    for genre in top_100_charts:
        print("\n***** {} *****".format(genre))
        dump_tracks(top_100_charts[genre])
        print("\n\n")
        spotify.add_new_tracks_to_playlist(genre, top_100_charts[genre])

    end_time = datetime.now()
    print("\n[!] Done @ {}\n (Ran for: {})".format(end_time, end_time - start_time))
