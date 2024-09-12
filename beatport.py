import json
import re
import sys
import requests
from config import genres


# Since genre list is calculated in javascript, we need to render the page to get it
def render_page(url):
    from selenium import webdriver
    import time

    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(3)
    r = driver.page_source
    driver.quit()
    return r


def get_chart_genres():
    from bs4 import BeautifulSoup

    available_genres = dict()
    r = requests.get("https://www.beatport.com/charts")
    soup = BeautifulSoup(r.text)
    genre_list_items = (
        soup.find("div", {"class": "bucket genre-list"})
        .find("ul", {"class": "bucket-items"})
        .find_all("li")
    )
    for genre in genre_list_items:
        available_genres[genre.find("a").text] = genre.find("a").get("href")
    return available_genres


def get_genres():
    from bs4 import BeautifulSoup

    available_genres = {"All Genres": ""}
    r = render_page("https://www.beatport.com/")
    soup = BeautifulSoup(r, "html.parser")
    links = soup.find_all(
        "a", {"data-testid": re.compile(r"header-subnav-link-genre\d*")}
    )
    for genre in links:
        available_genres[genre.text] = genre.get("href").replace("/genre/", "")
    return available_genres


def get_top_100_playables(genre):
    from bs4 import BeautifulSoup

    # Realistic headers to circumvent lockout for too many requests
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    }
    r = requests.get(
        "https://www.beatport.com/{}/{}/top-100".format(
            "genre" if genres[genre] else "", genres[genre]
        ),
        headers=HEADERS,
    )
    if r.status_code == 403:
        print("Forbidden error:")
        print(r.text)
        sys.exit()
    soup = BeautifulSoup(r.text, "html.parser")
    next_data = soup.find("script", {"id": "__NEXT_DATA__"})
    return json.loads(next_data.contents[0])["props"]["pageProps"]["dehydratedState"][
        "queries"
    ][0]["state"]["data"]["results"]


def parse_tracks(tracks_json):
    tracks = list()
    for track in tracks_json:
        tracks.append(
            {
                "title": (
                    track["release"]["name"]
                    if track["release"]["name"]
                    else track["name"]
                ),
                "name": track["name"],
                "mix": track["mix_name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "remixers": [remixer["name"] for remixer in track["remixers"]],
                "release": track["release"]["name"],
                "published_date": track["publish_date"],
                "duration": track["length"],
                "duration_ms": track["length_ms"],
                "genres": track["genre"]["name"],
                "bpm": track["bpm"],
                "key": track["key"]["name"],
            }
        )
    return tracks


def get_top_100_tracks(genre):
    print("[+] Fetching Top 100 {} Tracks".format(genre))
    raw_tracks_dict = get_top_100_playables(genre)
    return parse_tracks(raw_tracks_dict)
