import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import requests
from _utils import *
from _mood_settings import *

fastapi_url = 'http://fastapi:8000'

@st.cache_data(ttl=600)
def pull_genre_payload():
    genres_raw = requests.get(f'{fastapi_url}/genres/')
    return genres_raw.json()['genres']

def pull_unique_genres(genres):
    genres = [i for i in genres]
    return sort_list(genres)

def pull_unique_subgenres(genres):
    subgenres = []
    for i in genres.values():
        subgenres += i
    return sort_list(subgenres)

# @st.cache_data(ttl=600)
def initiate_genres():
    if 'genres_payload' not in st.session_state:
        st.session_state.genres_payload = pull_genre_payload()
    if 'all_genres' not in st.session_state:
        st.session_state.all_genres = pull_unique_genres(st.session_state.genres_payload)
    if 'all_subgenres' not in st.session_state:
        st.session_state.all_subgenres = pull_unique_subgenres(st.session_state.genres_payload)

@st.cache_data(ttl=600)
def pull_artist_payload():
    artists_raw = requests.get(f'{fastapi_url}/artists/')
    return artists_raw.json()['artists']

def pull_unique_artists(artists):
    artists = [i for i in artists]
    return sort_list(artists)

def initiate_artists():
    if 'all_artists' not in st.session_state:
        st.session_state.artists_payload = pull_artist_payload()
        st.session_state.all_artists = pull_unique_artists(st.session_state.artists_payload)

@st.cache_data(ttl=600)
def pull_publication_payload():
    publications_raw = requests.get(f'{fastapi_url}/publications/')
    return publications_raw.json()['publications']

def pull_unique_publications(publications):
    publications = [i for i in publications]
    return sort_list(publications)

def initiate_publications():
    if 'all_publications' not in st.session_state:
        st.session_state.publications_payload = pull_publication_payload()
        st.session_state.all_publications = pull_unique_publications(st.session_state.publications_payload)

def retrieve_artist_id(artist):
    return st.session_state.artists_payload[artist]

def retrieve_album_id(album):
    return st.session_state.albums_payload[album]

def retrieve_track_id(track):
    for tracks in st.session_state.tracks_payload:
        if tracks['track_name'] == track:
            return tracks['track_id']


@st.cache_data(ttl=600)
def retrieve_albums_payload(artist_id=None):
    if artist_id:
        artists_raw = requests.get(f'{fastapi_url}/albums_for_artist/{artist_id}')
        return artists_raw.json()['albums']

def pull_unique_albums(albums):
    if albums:
        albums = [i for i in albums]
    else:
        albums = []
    return sort_list(albums)

@st.cache_data(ttl=600)
def retrieve_tracks_payload(artist_id=None, album_id=None, album_ids=None):
    if album_ids is not None:
        base_id = f'{fastapi_url}/tracks_for_albums/?'
        for album in album_ids:
            base_id += f'&album_ids={album}'
        #print(base_id)
        tracks_raw = requests.get(base_id)
    elif album_id is not None:
        base_id = f'{fastapi_url}/tracks_for_album/{album_id}'
        tracks_raw = requests.get(base_id)
    elif artist_id is not None:
        base_id = f'{fastapi_url}/tracks_for_artist/{artist_id}'
        tracks_raw = requests.get(base_id)
    else:
        tracks_raw = None
    return tracks_raw.json()['tracks']

def pull_unique_tracks(tracks):
    if tracks:
        tracks = [i['track_name'] for i in tracks]
    else:
        tracks = []
    return sort_list(tracks)


@st.cache_data(ttl=600)
def retrieve_popular_tracks(artist_id, album_id=None):
    if album_id:
        tracks_raw = requests.get(f'{fastapi_url}/random_track_from_album/{album_id}')
    else:
        tracks_raw = requests.get(f'{fastapi_url}/random_track_from_artist/{artist_id}')
    track_name = [i for i in tracks_raw.json()['tracks']][0]
    return tracks_raw.json()['tracks'][track_name]['track_id']

#@st.cache_data(ttl=600)
def get_track_info(track_id, 
                   request_length=50, 
                   restrict_genre=False, 
                   duration_min_minute=True, 
                   unskew_features=True
                   ):
    if duration_min_minute:
        duration_min = 60000
    else:
        duration_min = 0
    base_url = f'{fastapi_url}/get_similar_tracks_total/{track_id}?restrict_genre={restrict_genre}&request_length={request_length}&duration_min={duration_min}'
    df = requests.get(base_url)
    df = pd.DataFrame.from_dict(df.json()['tracks'], orient='index')
    return df

def get_track_info_mood(mood, genres):
    base_url = f'{fastapi_url}/get_tracks_by_features/?'
    mood_object = mood_dictionary[mood]
    base_url = add_musical_features_to_base_url(mood_object, base_url)
    mood_object.import_custom_genres(genres)
    base_url = add_genres_to_remove(mood_object, base_url)
    print(base_url)
    df = requests.get(base_url)
    df = pd.DataFrame.from_dict(df.json()['tracks'], orient='index')
    return df

@st.cache_data(ttl=600)
def get_relevant_albums(min_year, 
                        max_year, 
                        genre=None, 
                        subgenre=None, 
                        publication=None, 
                        list=None
                        ):
    base_api = f'{fastapi_url}/get_relevant_albums/?min_year={min_year}&max_year={max_year}'
    if genre:
        for item in genre:
            if item == 'R&B':
                item = 'R%26B'
            base_api += f'&genre={item}'
    else:
        base_api += '&genre='
    if subgenre:
        for item in subgenre:
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

def return_tracks(albums, 
                  random_order=True, 
                  track_length=50, 
                  replace_albums=True, 
                  weight_albums=True, 
                  weight_tracks=True,
                  album_limit=500
                  ):
    # Reweight Ranks
    albums = albums[:album_limit]
    albums['weighted_rank_pct'] = reweight_list(albums['weighted_rank'])
    if replace_albums == False:
        request_length = min(track_length, len(df))
        album_choice = np.random.choice(albums['album_id'], 
                                        replace=replace_albums, 
                                        size=request_length, 
                                        p=albums['weighted_rank_pct'])
    else:
        album_selection = list(albums['album_id'])
        weighted_rank = list(albums['weighted_rank_pct'])
        album_choice = []
        max_occurrence_count = max(3, (track_length // len(albums)) + 1) #hardcoded right now
        # sloppy custom way to limit random selection so top albums aren't overpulled in smaller pools
        for i in range(track_length):
            result = np.random.choice(album_selection, 
                                      replace=True, 
                                      size=1, 
                                      p=weighted_rank)[0]
            album_choice.append(result)
            occurrence_count = album_choice.count(result)
            if occurrence_count >= max_occurrence_count:
                item_index = album_selection.index(result)
                del album_selection[item_index]
                del weighted_rank[item_index]
                weighted_rank = normalize_weights(weighted_rank)
    track_results = retrieve_tracks_payload(album_ids=album_choice)
    tracks = pd.DataFrame(track_results)
    final_tracks = []
    for album in album_choice:
        available = len(tracks[tracks['album_id'] == album]['track_id'])
        if available > 0:
            track_to_add = np.random.choice(tracks[tracks['album_id'] == album]['track_id'])
            final_tracks.append(track_to_add)
            tracks = tracks[tracks['track_id'] != track_to_add].reset_index(drop=True)
    df = pd.DataFrame()
    df['tracks'] = final_tracks
    track_results_two = pd.DataFrame(track_results)
    df = df.merge(pd.DataFrame(track_results_two), left_on='tracks', right_on='track_id')
    df.index = df['tracks']
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

# @st.cache_data
def get_album_accolades_multiple_albums(album_ids, n_accolades=10):
    base_id = f'{fastapi_url}/get_album_accolades_multiple_albums/?'
    for album in album_ids:
        base_id += f'&album_ids={album}'
    accolades = requests.get(base_id)
    if accolades.status_code == 200:
        return accolades.json()['albums']

# @st.cache_data
def show_albums(df, list_start=0, list_end=100, show_subgenres=None):
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

# @st.cache_data
def show_albums_two(df, list_start=0, list_end=50, show_subgenres=None):
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

