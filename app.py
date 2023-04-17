from flask import Flask, render_template, redirect, url_for, request, session
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import random
import time

CLIENT_ID = "415febb0f5484f57bb3d6a0c35af9ee3"
CLIENT_SECRET = "f70ed50aca0947bab43ea4732135c593"
REDIRECT_URL = "http://127.0.0.1:5001/callback"
SCOPES = '''user-read-private user-read-email user-read-currently-playing streaming user-read-recently-played user-top-read user-read-playback-state user-library-read user-library-modify playlist-modify-private playlist-modify-public'''


app = Flask(__name__)


app.config["SPOTIFY_COOKIES"] = 'Spotify Cookie'
app.secret_key = 'some random'

TOKEN_INFO = 'token_info'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    print(auth_url)
    return redirect(auth_url)


@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('create_weekly_playlist', _external=True))


@app.route('/create')
def create_weekly_playlist():
    try:
        token = get_token()
    except:
        print('User not logged in')
        return redirect("/")

    print("Your Access Token Is: ", token)

    sp = spotipy.Spotify(auth=token['access_token'])
    user_playlists = sp.current_user_playlists()['items']

    top_artists = sp.current_user_top_artists()['items']
    top_tracks = sp.current_user_top_tracks()['items']
    print("Top Tracks",top_tracks)
    genres = sp.recommendation_genre_seeds()
    genres = genres['genres']
    random_number = random.randint(0, len(genres))
    genre = genres[random_number]

    artists = []
    tracks = []
    for artist in top_artists:
        artists.append(artist["id"])

    for track in top_tracks:
        tracks.append(track["id"])

   
    
    print( len(artists), len(artists))

    recommendations = sp.recommendations(
        [artists[0]], [genre], [tracks[0]], 20, 'IN')

    print("Recommendations", recommendations)

    discover_weekly_playlist_id = None

    for playlist in user_playlists:
        if playlist['name'] == 'Discover Weekly':
            discover_weekly_playlist_id = playlist['id']

    song_uris = []

    for song in recommendations["tracks"]:
        song_uris.append(song['uri'])

    # append this songs to discover weekly

    sp.user_playlist_add_tracks(
        '31kve4nnchjjq6l72tn7ptzdlqa4', discover_weekly_playlist_id, song_uris)

    return "Plalist songs added"


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URL,
        scope=SCOPES
    )


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))

    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(
            token_info['refresh_token'])

    return token_info


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)