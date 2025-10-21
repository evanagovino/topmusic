import streamlit as st
import numpy as np
from query_commands import *
from _utils import *

def radio_type_callback():
    st.write(st.session_state.radio_type)
    if st.session_state.radio_type == 'Genre':
        for values in ['artist_id', 'artist_selection']:
            if values in st.session_state:
                del st.session_state[values]
    elif st.session_state.radio_type == 'Artist':
        for values in ['genre_selection', 'subgenre_selection']:
            if values in st.session_state:
                del st.session_state[values]
    elif st.session_state.radio_type == 'Mood':
        for values in ['mood_selection']:
            if values in st.session_state:
                del st.session_state[values]

def genre_callback():
    if 'genre_selection' in st.session_state:
        if st.session_state.genre_selection in st.session_state.genres_payload:
            st.session_state.available_subgenres = st.session_state.genres_payload[st.session_state.genre_selection]
            if 'All' not in st.session_state.available_subgenres:
                st.session_state.available_subgenres.append('All')
            st.session_state.available_subgenres.sort(key=lambda x: "0" if x == 'All' else x)
        else:
            st.session_state.available_subgenres = st.session_state.all_subgenres
    else:
        st.session_state.available_subgenres = st.session_state.all_subgenres


def artist_callback():
    if 'artist_selection' in st.session_state and st.session_state.artist_selection != 'All':
        st.session_state.artist_id = retrieve_artist_id(st.session_state.artist_selection)
        st.session_state.albums_payload = retrieve_albums_payload(artist_id=st.session_state.artist_id)
        st.session_state.available_albums = pull_unique_albums(st.session_state.albums_payload)
        st.session_state.tracks_payload = retrieve_tracks_payload(artist_id=st.session_state.artist_id)
        st.session_state.available_tracks = pull_unique_tracks(st.session_state.tracks_payload)

def album_callback():
    if 'album_selection' in st.session_state:
        if st.session_state.album_selection == 'All':
            del st.session_state['album_selection']
        else:
            st.session_state.album_id = retrieve_album_id(st.session_state.album_selection)
            st.session_state.tracks_payload = retrieve_tracks_payload(album_id=st.session_state.album_id)
    elif 'artist_id' in st.session_state:
        st.session_state.tracks_payload = retrieve_tracks_payload(artist_id=st.session_state.artist_id)
    if 'tracks_payload' in st.session_state:
        st.session_state.available_tracks = pull_unique_tracks(st.session_state.tracks_payload)

def song_callback():
    if 'song_selection' in st.session_state:
        if st.session_state.song_selection == 'All':
            del st.session_state.song_selection
        else:
            st.session_state.track_id = retrieve_track_id(st.session_state.song_selection)

def radio_callback(album_limit=100):
    if st.session_state.radio_type == 'Artist':
        st.session_state.track_info = get_recommended_tracks(artist_id=st.session_state.artist_id)
    elif st.session_state.radio_type == 'Genre':
        if 'genre_selection' in st.session_state:
            show_genres = [st.session_state.genre_selection]
            if 'subgenre_selection' in st.session_state:
                show_subgenres = [st.session_state.subgenre_selection]
            else:
                show_subgenres = None
        elif 'subgenre_selection' in st.session_state:
            show_subgenres = [st.session_state.subgenre_selection]
            show_genres = None
        if show_genres or show_subgenres:
            relevant_albums = get_relevant_albums(min_year = st.session_state.min_year,
                                                  max_year = st.session_state.max_year,
                                                  genre = show_genres,
                                                  subgenre = show_subgenres)
            if len(relevant_albums) > 0:
                st.session_state.track_info = return_tracks(relevant_albums, album_limit=album_limit)
    elif st.session_state.radio_type == 'Custom Prompt':
        st.session_state.track_info = get_recommended_tracks_from_custom_prompt(custom_prompt=st.session_state.custom_prompt)
        
        