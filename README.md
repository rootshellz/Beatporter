# Beatporter

This tool scrapes [Beatport's](https://www.beatport.com/) [DJ Charts](https://www.beatport.com/charts), by genre, and attempts to locate the tracks on Spotify and add them to genre-based playlists.

For each genre, new Spotify playlists will be created and / or updated based on the most recent Beatport charts. Not all tracks from the charts will be available on Spotify and some tracks may be different mixes (if the exact mix is not available).

This tool currently supports toggleable genre settings and creates two playlists per enabled genre:

- Daily Top 10 - Contains all available songs from the given genre's current Top 10 Chart, the playlist is cleared and repopulated every time the tool is run.
- Cumulative Top 100 - Contains all available songs from the given genre's Top 100 Chart, adding songs every time the tool is run. The playlist is created on the first run, then songs are cumulatively added on all subsequent runs. Song are only ever added to the playlist once, even if they appear on the Top 100 chart across multiple runs. Effectively, this is a cumulatively, deduplicated, playlist of the Top 100 Chart over time.

There is also support for the genre-agnostic, overall, Top 10 and Top 100 charts.

## Prerequisites

- Python 3
- Spotify Account
- Create / register an app on the [Spotify Developer](https://developer.spotify.com) site
  - Add the `redirect_uri` value to the _Redirect URIs_ within the app dashboard. The value added to the dashboard must match the variable exactly.

### Python 3 Packages

- spotipy (tested up to 2.17.1)

```sh
pip install spotipy
```

- beautifulsoup4 (tested with 4.9.3)

```sh
pip install beautifulsoup4
```

- selenium (tested with 4.24.0)

```sh
pip install selenium
```

## Configuration

- Copy config.example.py to config.py and update the following values:
  - `username` is your Spotify username
  - `user_id` is your Spotify user_id that can be found in your profile's url `http://open.spotify.com/user/{{user_id}}`
  - `client_id` and `client_secret` are values provided by Spotify for your registered app (on the [Spotify Developer](https://developer.spotify.com) site under the app dashboard).
  - `redirect_uri` this is the local listener that is used to intercept the Spotify authentication callback.
    - As described above, the `redirect_uri` needs to be registered verbatim on the [Spotify Developer](https://developer.spotify.com) site. Go to the app's dashboard and click _Edit Settings_. Then under _Redirect URIs_ paste the value of `redirect_uri` and click _add_. Finally, scroll to the bottom of the _Edit Settings_ window and click _Save_.
  - `genres` is a dictionary that maps genre names (which are arbitrary and will be used in playlist names) to Beatport URL components.
    - The presence of a genre in the dictionary toggles it on (its absence toggles it off)
      - Simply comment out (or remove) the line for a genre to stop it from syncing
    - The URL component comes from the way Beatport structures their genre chart URLs.
      - For example, the Top 100 chart for Trance is at the URL `https://www.beatport.com/genre/trance/7/top-100`, so the URL component in the dictionary is `trance/7`
    - All known genres and their URL component mapping are included in the example config for easy reference.
      - If you know of other (hidden) genre URLs, please share in an issue or PR.

## Authentication

This application will never see your Spotify credentials. Instead, upon successful authentication and approval, Spotify will provide this application with an API token that can be used to read and modify your library and playlists.

### Initial Authentication & Application Approval

The first time you run the application your web browser should open to the Spotify authentication page. Upon successful authentication, you will be prompted to approve this application with the permission scope defined in the `config.scope` variable. If approved, Spotify will "callback" to the application and provide the necessary API tokens.

After authenticating, your browser may display something like "This page isn’t working localhost didn’t send any data." This is okay, simply close the window and you should see the application working.

### Token Refresh

The API token provided by Spotify is short-lived, however, a refresh token is aso provided during authentication. This refresh token can be used to retrieve a new API token (and a new refresh token) in the future. These tokens are persisted to disk at `token.json` and `.cache-USERNAME`.

### Token Security

The `token.json` and `.cache-USERNAME` files should be protected from unauthorized access as the tokens contained within can be used to read your Spotify library and modify playlists. If you are paranoid, you can simply remove these files manually after running the application. You will simply need to go through the Spotify webpage authentication cycle again instead of having transparent auth via refresh. If your authentication is cached in your browser this will happen automatically. You will also not need to re-approve the app (unless the scope in the `config.scope` variable has changed).

Your Spotify credentials are _not_ stored in these files. The tokens in these files cannot be used to gain additional permissions. Token permission scope is bound to whatever was in the `config.scope` variable at the time of initial application approval.

## Running

To run the application:

`python3 beatporter.py`

### Get Updated Genres

[Beatport](https://www.beatport.com/) often updates their [genres](https://www.beatport.com/charts) (and the URLs used by Beatporter to retrieve songs from the charts). To retrieve the current list of genres and links directly from Beatport, run:

`python3 beatporter.py --genres`

This will output a Python dictionary / JSON string object that can be pasted directly into the active configuration file (_config.py_).

Note: Any differences in genre naming will cause a new playlist to be created; If instead, you would like an existing playlist to adopt the new (or renamed) genre, simply rename the playlist manually in Spotify before running Beatporter with the new genre in the config.

## Future Features / ToDo

This project was born out of a personal desire for this functionality. I've continued to use and tweak the tool locally for years. However, I've recently noticed there are at least a couple of other active users out there, so better maintenance and development practices can be followed. There is a lot that can be done to clean this up if there is continued outside interest.

- Start using a better development process
  - Branches and PRs for everything (no more random commits to master)
  - Check issues once in a while
  - Audit and clean up the code base
    - e.g. Recently implemented a caching fix that significantly decreased overall run time and reduced the number of Spotify API calls by an order of magnitude.
    - Even with the above fix, there is probably room for better timeout and rate-limit handling.
  - Update genres in the example config more often.
    - Manual updates are now supported using [`python3 beatporter.py --genres`](#get-updated-genres)
    - It would be cool to have this automatically update the repo in the future.
- Implement user-configurable playlists
  - Allow toggling of which playlists the user wants to be updated
  - Support Cumulative Top 10 & Daily Top 100 (Currently only Daily Top 10 and Cumulative Top 100 exist)
  - Support arbitrarily sized playlists (Top X - Top 100), configurable to be cleared on each run or be cumulative
  - Support arbitrarily named playlists, as configured by the user
- Authentication process could be better
  - Implement a real HTTP listener that can return an actual HTTP response with a pretty HTML page.
    - Currently, a hacky TCP socket listener is used. It's not pretty, but it works.
  - Cleanup token caching
    - Use only `.cache-USERNAME` instead of `token.json`
    - Add option to auto delete on completion
- Implement this as a web app
  - Others could auth and use the app without running it themselves
- Maintain curated, public Spotify playlists
  - I could simply maintain the playlists myself and make them public for consumption without everyone syncing their own playlists.
