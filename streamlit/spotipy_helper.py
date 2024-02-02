import os
import spotipy
from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import time

class StreamlitSessionCacheHandler(CacheHandler):
    """
    A cache handler that stores the token info in the session framework
    provided by flask.
    """

    def __init__(self, session):
        self.session = session

    def get_cached_token(self):
        token_info = None
        try:
            token_info = self.session["token_info"]
            print("Token found in session")
        except KeyError:
            print("Token not found in the session")

        return token_info

    def save_token_to_cache(self, token_info):
        try:
            self.session["token_info"] = token_info
            print("Token saved to cache")
        except Exception as e:
            print("Error saving token to cache: " + str(e))

def get_access_token(auth_manager, code=None):
    return auth_manager.get_cached_token(code)

def spotipy_error_message(func):
    def wrapper(*args, **kwargs):
        if 'client_creds' in kwargs:
            pass
        elif 'spotify' not in st.session_state:
            st.session_state.spotify = spotipy.Spotify(auth_manager=st.session_state.auth_manager)
        try:
            st.session_state.spotipy_error = None
            try:
                return func(*args, **kwargs)
            except:
                time.sleep(1)
                return func(*args, **kwargs)

        except spotipy.exceptions.SpotifyException as e:
            if 'User not registered in the Developer Dashboard' in e.msg:
                st.session_state.spotipy_error = 'User not registered in the developer dashboard'
            elif 'Player command failed: Premium required' in e.msg:
                st.session_state.spotipy_error = 'Spotify Premium required for this feature'
            elif e.reason == 'NO_ACTIVE_DEVICE':  
                st.session_state.spotipy_error = 'No active device. Press play on your Spotify player and try again'
            else:
                st.session_state.spotipy_error = e.msg
        else:
            st.session_state.spotipy_error = 'Unable to initiate playback. Perhaps you are not a Premium member?'
    return wrapper

@spotipy_error_message
def spotipy_album_request(album_uris, client_creds=True):
    return st.session_state.spotify_client_creds.albums(album_uris)

@spotipy_error_message
def spotipy_track_request(track_uris, client_creds=True):
    return st.session_state.spotify_client_creds.tracks(track_uris)

@spotipy_error_message
def spotipy_start_playback(uris=None):
    return st.session_state.spotify.start_playback(uris=uris)

@spotipy_error_message
def spotipy_pause_playback():
    if 'device_id' in st.session_state:
        return st.session_state.spotify.pause_playback(device_id=st.session_state.device_id)
    else:
        return st.session_state.spotify.pause_playback()

@spotipy_error_message
def spotipy_previous_track():
    return st.session_state.spotify.previous_track()

@spotipy_error_message
def spotipy_next_track():
    if 'device_id' in st.session_state:
        return st.session_state.spotify.next_track(device_id=st.session_state.device_id)
    else:
        return st.session_state.spotify.next_track()

@spotipy_error_message
def spotipy_current_playback():
    if 'device_id' in st.session_state:
        return st.session_state.spotify.current_playback(device_id=st.session_state.device_id)
    return st.session_state.spotify.current_playback()

# @st.cache_data
def spotipy_currently_playing(time_sleep=0, max_time_sleep=2):
    time.sleep(time_sleep)
    try:
        current_song = st.session_state.spotify.currently_playing()
        payload = {'song_name': current_song['item']['name'],
                   'artist_name': ', '.join([artist['name'] for artist in current_song['item']['artists']]),
                   'album_name': current_song['item']['album']['name'],
                   'album_url': current_song['item']['album']['images'][0]['url'],
                   'album_link': current_song['item']['album']['external_urls']['spotify']
                  }
        return payload

    except Exception as e:
        time_sleep += 1
        if time_sleep < max_time_sleep:
            spotipy_currently_playing(time_sleep=time_sleep)

@spotipy_error_message
def spotipy_me():
    return st.session_state.spotify.me()

@spotipy_error_message
def spotipy_user_playlist_create(user, playlist_name):
    return st.session_state.spotify.user_playlist_create(user=user, name=playlist_name)

@spotipy_error_message
def spotipy_user_playlist_add_tracks(user, playlist_id, tracks):
    return st.session_state.spotify.user_playlist_add_tracks(user, playlist_id=playlist_id, tracks=tracks)

def spotify_create_playlist(tracks, year, genre, publication):
    user = spotipy_me()
    if user and tracks:
        user_id = user['id']
        playlist_name = f'TopMusic.Page - {year} {genre} {publication}'
        playlist = spotipy_user_playlist_create(user_id, playlist_name)
        spotipy_user_playlist_add_tracks(user_id, playlist['id'], tracks)
        st.session_state.playlist_id = playlist['id']

def setup_auth_manager():
    cache_handler = StreamlitSessionCacheHandler(st.session_state)
    auth_manager = SpotifyOAuth(scope='streaming user-read-playback-state playlist-modify-public',
                                cache_handler=cache_handler
                                )
    return auth_manager

def spotipy_setup():
    st.session_state['SPOTIPY_CLIENT_ID'] = os.environ['SPOTIPY_CLIENT_ID']
    st.session_state['SPOTIPY_CLIENT_SECRET'] = os.environ['SPOTIPY_CLIENT_SECRET']
    st.session_state['SPOTIPY_REDIRECT_URI'] = os.environ['SPOTIPY_REDIRECT_URI']
    st.session_state.spotipy_error = None
    if 'list_start' not in st.session_state:
        st.session_state.list_start = 0
    if 'playlist_id' not in st.session_state:
        st.session_state.playlist_id = None
    if 'spotify_client_creds' not in st.session_state:
        client_creds = spotipy.SpotifyClientCredentials(
            client_id=st.session_state['SPOTIPY_CLIENT_ID'],
            client_secret=st.session_state['SPOTIPY_CLIENT_SECRET']
            )
        st.session_state.spotify_client_creds = spotipy.Spotify(client_credentials_manager=client_creds)
    url_params = st.query_params
    if 'code' in url_params:
        print('code acknowledged', url_params['code'])
        st.session_state.code = url_params['code']
        try:
            if 'auth_manager' not in st.session_state:
                st.session_state.auth_manager= setup_auth_manager()
            st.session_state.token_info = st.session_state.auth_manager.get_access_token(st.session_state.code)
            print('token', st.session_state.token_info)
            st.session_state.spotify = spotipy.Spotify(auth_manager=st.session_state.auth_manager)
        except Exception as e:
            print(e)
    else:
        print('code not acknowledged', url_params)

def spotify_player():
    with st.sidebar:
        if st.session_state.spotipy_error:
            st.write(st.session_state.spotipy_error) 
        else:
            if 'spotify' in st.session_state:
                if 'playlist_id' in st.session_state:
                    if st.session_state['playlist_id']:
                        playlist_link = f'https://open.spotify.com/playlist/{st.session_state.playlist_id}'
                        link = f'[Click here to see your created playlist]({playlist_link})'
                        st.markdown(link, unsafe_allow_html=True)
                payload = spotipy_currently_playing(time_sleep=0, max_time_sleep=2)
                if payload:
                    st.image('https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png', width=100)
                    st.write('Now Playing:')
                    st.write(payload['artist_name'])
                    st.write(payload['song_name'])
                    st.markdown(f"[{payload['album_name']}]({payload['album_link']})")
                    if 'album_url' in payload:
                        st.image(payload['album_url'])
            else:
                if 'auth_manager' not in st.session_state:
                    st.session_state.auth_manager= setup_auth_manager()
                auth_url = st.session_state.auth_manager.get_authorize_url()
                link = f'[Authenticate Here to Create Custom Playlists]({auth_url})'
                st.markdown(link, unsafe_allow_html=True)


