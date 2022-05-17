from flask import abort, Flask, redirect, render_template, request, session, url_for
import json
import logging
import os
from os import environ, path
import requests
from dotenv import load_dotenv

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

# ENVIRONMENT CONFIG
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
SEARCH_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'search?')
ME_URL = 'https://api.spotify.com/v1/me'
REDIRECT_URI = 'http://127.0.0.1:5000/callback'


app = Flask(__name__)

# Client Info
CLIENT_ID = environ.get('CLIENT_ID')
CLIENT_SECRET = environ.get('CLIENT_SECRET')
app.secret_key = environ.get('SECRET_KEY')



@app.route('/')
def index():

    return render_template('index.html')


@app.route('/auth')
def auth():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
    }

    url_args = "&".join(["{}={}".format(key, val) for key, val in params.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)

    return redirect(auth_url)


@app.route('/callback')
def callback():
    # Requests refresh and access tokens
    auth_token = request.args['code']
    payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=payload)

    response_data = post_request.json()

    if response_data.get('error') or post_request.status_code != 200:
        app.logger.error(
            'Failed to receive token: %s',
            response_data.get('error', 'No error information received.'),)
        abort(post_request.status_code)

    # Load tokens into session
    session['tokens'] = {
        'access_token': response_data.get('access_token'),
        'refresh_token': response_data.get('refresh_token'),
    }

    return redirect(url_for('search'))


def _query(track=None, artist=None):
    if track is None:
        return track

    headers = {
        'Authorization': "Bearer {}".format(session['tokens'].get('access_token')),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    return requests.get(SEARCH_ENDPOINT + "q={}%20{}&type=track%2Cartist".format(track, artist), headers=headers)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':

        track = request.form.get('track')
        artist = request.form.get('artist')

        if track:
            res = _query(track, artist)
            response_data = res.json()
            print('\n'*10)
            print(response_data)
            print('\n'*10)

            if response_data['artists']['items'] == [] and response_data['tracks']['items'] == []:
                return render_template('search.html', error_msg='No results - try again')
            else:
                image_url = response_data['tracks']['items'][0]['album']['images'][0]['url']
            
            return render_template('search.html', image=image_url)

        else:
            return render_template('search.html', error_msg='No track entered')

    else:
        return render_template('search.html', image=None)

@app.route('/error')
def error():
    return render_template('error.html')