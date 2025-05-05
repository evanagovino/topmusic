import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import requests
from _utils import *
from _mood_settings import *

fastapi_url = 'http://fastapi:8000'

# Genre Functions

@st.cache_data(ttl=600)
def pull_genre_payload() -> dict:
    """
    Returns dictionary of genres, with associated subgenres
    """
    genres_raw = requests.get(f'{fastapi_url}/web/genres/')
    return genres_raw.json()['genres']

def pull_unique_genres(genres: dict) -> list:
    """
    Returns list of unique genres, sorted by name
    """
    genres = [i for i in genres]
    return sort_list(genres)

def pull_unique_subgenres(genres: dict) -> list:
    """
    Returns list of unique subgenres, sorted by name
    """
    subgenres = []
    for i in genres.values():
        subgenres += i
    return sort_list(subgenres)

# @st.cache_data(ttl=600)
def initiate_genres():
    """
    Function to add genre payload, list of genres, and list of subgenres to Streamlit session
    """
    if 'genres_payload' not in st.session_state:
        st.session_state.genres_payload = pull_genre_payload()
    if 'all_genres' not in st.session_state:
        st.session_state.all_genres = pull_unique_genres(st.session_state.genres_payload)
    if 'all_subgenres' not in st.session_state:
        st.session_state.all_subgenres = pull_unique_subgenres(st.session_state.genres_payload)

# Artist Functions

@st.cache_data(ttl=600)
def pull_artist_payload() -> dict:
    """
    Returns dictionary of artists, with associated Artist IDs (note these are Spotify IDs) 
    """
    artists_raw = requests.get(f'{fastapi_url}/web/artists/')
    return artists_raw.json()['artists']

def pull_unique_artists(artists: dict) -> list:
    """
    Returns sorted list of unique artists
    """
    artists = [i for i in artists]
    return sort_list(artists)

def initiate_artists():
    """
    Function to add artist payload and list of artists to Streamlit session
    """
    if 'all_artists' not in st.session_state:
        st.session_state.artists_payload = pull_artist_payload()
        st.session_state.all_artists = pull_unique_artists(st.session_state.artists_payload)

# Publication Functions

@st.cache_data(ttl=600)
def pull_publication_payload() -> dict:
    """
    Returns dictionary of publications, with associated lists
    """
    publications_raw = requests.get(f'{fastapi_url}/web/publications/')
    return publications_raw.json()['publications']

def pull_unique_publications(publications: dict) -> list:
    """
    Returns sorted list of unique publications
    """
    publications = [i for i in publications]
    return sort_list(publications)

def initiate_publications():
    """
    Add publication payload and list of publications to Streamlit session
    """
    if 'all_publications' not in st.session_state:
        st.session_state.publications_payload = pull_publication_payload()
        st.session_state.all_publications = pull_unique_publications(st.session_state.publications_payload)

def retrieve_artist_id(artist: str) -> str:
    """
    Returns artist ID based on artist name
    """
    return st.session_state.artists_payload[artist]

def retrieve_album_id(album: str) -> str:
    """
    Returns album ID based on album name
    """
    return st.session_state.albums_payload[album]

def retrieve_track_id(track: str) -> str:
    """
    Returns track ID based on a track name
    """
    for tracks in st.session_state.tracks_payload:
        if tracks['track_name'] == track:
            return tracks['track_id']


@st.cache_data(ttl=600)
def retrieve_albums_payload(artist_id: str = None) -> dict:
    """
    Returns payload of albums based on an artist ID
    """
    if artist_id:
        artists_raw = requests.get(f'{fastapi_url}/web/albums_for_artist/{artist_id}')
        return artists_raw.json()['albums']

def pull_unique_albums(albums: dict) -> list:
    """
    Returns list of unique albums based on a payload of albums
    """
    if albums:
        albums = [i for i in albums]
    else:
        albums = []
    return sort_list(albums)

@st.cache_data(ttl=600)
def retrieve_tracks_payload(artist_id: str = None, 
                            album_id: str = None, 
                            album_ids: list = None) -> dict:
    """
    Returns list of track IDs for a given input
    """
    if album_ids is not None:
        base_id = f'{fastapi_url}/web/tracks_for_albums/?'
        for album in album_ids:
            base_id += f'&album_ids={album}'
        tracks_raw = requests.get(base_id)
    elif album_id is not None:
        base_id = f'{fastapi_url}/web/tracks_for_album/{album_id}'
        tracks_raw = requests.get(base_id)
    elif artist_id is not None:
        base_id = f'{fastapi_url}/web/tracks_for_artist/{artist_id}'
        tracks_raw = requests.get(base_id)
    else:
        tracks_raw = None
    return tracks_raw.json()['tracks']

def pull_unique_tracks(tracks: dict) -> list:
    """
    Returns list of track names given a payload of track IDs
    """
    if tracks:
        tracks = [i['track_name'] for i in tracks]
    else:
        tracks = []
    return sort_list(tracks)


@st.cache_data(ttl=600)
def retrieve_popular_tracks(artist_id: str, 
                            album_id: str = None) -> str:
    """
    Returns randomized track ID given an artist ID or album ID
    """
    if album_id:
        tracks_raw = requests.get(f'{fastapi_url}/web/random_track_from_album/{album_id}')
    else:
        tracks_raw = requests.get(f'{fastapi_url}/web/random_track_from_artist/{artist_id}')
    track_name = [i for i in tracks_raw.json()['tracks']][0]
    return tracks_raw.json()['tracks'][track_name]['track_id']

#@st.cache_data(ttl=600)
def get_track_info(track_id: str, 
                   request_length: int = 50, 
                   restrict_genre: bool = False, 
                   duration_min_minute: bool = True, 
                   unskew_features: bool = True
                   ) -> pd.DataFrame:
    """
    Returns dataframe of similar tracks given a Track ID
    """
    if duration_min_minute:
        duration_min = 60000
    else:
        duration_min = 0
    base_url = f'{fastapi_url}/web/get_similar_tracks/{track_id}?restrict_genre={restrict_genre}&request_length={request_length}&duration_min={duration_min}'
    tracks = requests.get(base_url)
    # df = pd.DataFrame.from_dict(df.json()['tracks'], orient='index')
    df = pd.DataFrame(tracks.json()['tracks'])
    df.index = df['track_id']
    return df

def get_track_info_mood(mood: str, 
                        genres: list) -> pd.DataFrame:
    """
    Returns dataframe of recommended tracks given mood and list of genres
    """
    base_url = f'{fastapi_url}/web/get_tracks_by_features/?'
    mood_object = mood_dictionary[mood]
    base_url = add_musical_features_to_base_url(mood_object, base_url)
    mood_object.import_custom_genres(genres)
    base_url = add_genres_to_remove(mood_object, base_url)
    print(base_url)
    df = requests.get(base_url)
    df = pd.DataFrame.from_dict(df.json()['tracks'], orient='index')
    return df

@st.cache_data(ttl=600)
def get_relevant_albums(min_year: int, 
                        max_year: int, 
                        genre: str = None, 
                        subgenre: str = None, 
                        publication: str= None, 
                        list: str= None
                        ) -> pd.DataFrame:
    """
    Returns dataframe of relevant albums given year, genre, subgenre, publication, and list inputs
    """
    base_api = f'{fastapi_url}/web/get_relevant_albums/?min_year={min_year}&max_year={max_year}'
    if genre:
        for item in genre:
            item = item.replace('&', '%26')
            base_api += f'&genre={item}'
    else:
        base_api += '&genre='
    if subgenre:
        for item in subgenre:
            item = item.replace('&', '%26')
            base_api += f'&subgenre={item}'
    else:
        base_api += '&subgenre='
    if publication:
        for item in publication:
            base_api += f'&publication={item}'
    else:
        base_api += '&publication='
    if list:
        for item in list:
            base_api += f'&list={item}'
    else:
        base_api += '&list='
    relevant_albums = requests.get(base_api)
    result_df = pd.DataFrame.from_dict(relevant_albums.json()['albums'], orient='index')
    return result_df

def return_tracks(album_uris, 
                  random_order=True, 
                  track_length=50, 
                  replace_albums=True, 
                  weight_albums=True, 
                  weight_tracks=True,
                  album_limit=500
                  ):
    base_url = f'{fastapi_url}/web/return_tracks_from_albums/?'
    for album in album_uris['album_id'][:album_limit]:
        base_url += f'&album_uris={album}'
    base_url += f'&album_limit={album_limit}'
    tracks= requests.get(base_url)
    if tracks.status_code == 200:
        df = pd.DataFrame(tracks.json()['tracks'])
        df.index = df['track_id']
        return df

# @st.cache_data
def get_album_accolades(album_id, n_accolades=10):
    if 'album_accolades' in st.session_state:
        if st.session_state['album_accolades']:
            if album_id in st.session_state.album_accolades:
                accolades = st.session_state.album_accolades[album_id]
                for accolade in accolades:
                    publication = accolade['publication']
                    list = accolade['list']
                    rank = accolade['rank']
                    st.write(f'{publication} ({list}): {rank}')
            else:
                st.write('No Accolades Found For Album')

@st.cache_data
def get_album_accolades_multiple_albums(album_ids, n_accolades=10, album_limit=50):
    base_id = f'{fastapi_url}/web/get_album_accolades_multiple_albums/?'
    for album in album_ids[:album_limit]:
        base_id += f'&album_ids={album}'
    accolades = requests.get(base_id)
    if accolades.status_code == 200:
        return accolades.json()['albums']

# @st.cache_data
def show_albums(df, list_start=0, list_end=100, show_subgenres=None):
    try:
        unique_albums = list(df['album_id'].unique())
        st.session_state.album_accolades = get_album_accolades_multiple_albums(unique_albums)
        #print(st.session_state.album_accolades)
        for position in range(list_start, min(list_end, len(df))):
            album_key = df['album_id'][position]
            artist = df['artist'][position]
            album = df['album'][position]
            genre = df['genre'][position]
            subgenre = df['subgenre'][position]
            year = df['year'][position]
            image = df['image_url'][position]
            album_url = df['album_url'][position]
            col1, col2 = st.columns([1,1.4], gap='large')
            with col1:
                st.image(image, use_column_width=True)
            with col2:
                st.subheader(f'#{position + 1}')
                st.subheader(artist)
                st.subheader(album)
                if show_subgenres == None:
                    st.subheader(f'Genre: {genre}')
                else:
                    st.subheader(f'Genre: {subgenre}')
                st.subheader(year)
                container = st.expander('Accolades', expanded=False)
                with container:
                    get_album_accolades(album_key)
                container = st.expander('Listen', expanded=False)
                with container:
                    if album_url != '':
                        components.iframe(album_url, height=400)
                    else:
                        st.write('No streaming available for this album :(')
    except:
        st.write('No albums found for the selected parameters :(')

# @st.cache_data
def show_albums_two(df, list_start=0, list_end=50, show_subgenres=None):
    try:
        df['count'] = range(len(df))
        st.session_state.album_accolades = get_album_accolades_multiple_albums(list(df['album_id'].unique()))
        df = df.groupby(['album_id', 'artist', 'album_name', 'genre', 'subgenre', 'year', 'image_url', 'album_url'])['count'].min().reset_index().sort_values('count')
        df.index = range(len(df))
        bigcol1, bigcol2 = st.columns([1,1], gap='large')
        total_min = min(list_end, len(df))
        position = 0
        while (position + 1) < total_min:
            with bigcol1:
                    album_key = df['album_id'][position]
                    artist = df['artist'][position]
                    album = df['album_name'][position]
                    genre = df['genre'][position]
                    subgenre = df['subgenre'][position]
                    year = df['year'][position]
                    image = df['image_url'][position]
                    album_url = df['album_url'][position]
                    col1, col2 = st.columns([1,1.4], gap='large')
                    with col1:
                        st.image(image, use_column_width=True)
                    with col2:
                        st.subheader(artist)
                        st.subheader(album)
                        if show_subgenres == None:
                            st.subheader(f'Genre: {genre}')
                        else:
                            st.subheader(f'Genre: {subgenre}')
                        st.subheader(year)
                        container = st.expander('Accolades', expanded=False)
                        with container:
                            get_album_accolades(album_key)
                        container = st.expander('Listen', expanded=False)
                        with container:
                            if album_url != '':
                                components.iframe(album_url, height=400)
                            else:
                                st.write('No streaming available for this album :(')
            with bigcol2:
                    album_key = df['album_id'][position + 1]
                    artist = df['artist'][position + 1]
                    album = df['album_name'][position + 1]
                    genre = df['genre'][position + 1]
                    subgenre = df['subgenre'][position + 1]
                    year = df['year'][position + 1]
                    image = df['image_url'][position + 1]
                    album_url = df['album_url'][position + 1]
                    col1, col2 = st.columns([1,1.4], gap='large')
                    with col1:
                        st.image(image, use_column_width=True)
                    with col2:
                        st.subheader(artist)
                        st.subheader(album)
                        if show_subgenres == None:
                            st.subheader(f'Genre: {genre}')
                        else:
                            st.subheader(f'Genre: {subgenre}')
                        st.subheader(year)
                        container = st.expander('Accolades', expanded=False)
                        with container:
                            get_album_accolades(album_key)
                        container = st.expander('Listen', expanded=False)
                        with container:
                            if album_url != '':
                                components.iframe(album_url, height=400)
                            else:
                                st.write('No streaming available for this album :(')
            position += 2
    except:
        st.write('No albums found for the selected parameters :(')

