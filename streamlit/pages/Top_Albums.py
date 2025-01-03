import random
import datetime
import streamlit as st
import streamlit.components.v1 as components
from callbacks import *
from query_commands import *
from spotipy_helper import *

st.set_page_config('Top Albums', layout="wide")

page_header()

init_time = datetime.datetime.now()

initiate_genres()
initiate_artists()
initiate_publications()

spotipy_setup()

if 'track_info' in st.session_state:
    del st.session_state['track_info']

with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('[About](https://www.evanagovino.com/posts/why-does-topmusic-exist)')
    with col2:
        st.markdown('[Disconnect](https://topmusic.page)')
    year_selection = st.selectbox('One or Multiple Years?', ['One Year', 'Multiple Years'], index=0)
    if year_selection == 'One Year':
        show_years = st.selectbox('Year', list(range(2000,2025))[::-1], index=0)
        min_year = show_years
        max_year = show_years
        text_year = show_years
    else:
        col1, col2 = st.columns(2)
        with col1:
            min_year = st.selectbox('First Year', range(2000,2025), index=0)
        with col2:
            max_year = st.selectbox('Last Year', list(range(2000,2025))[::-1], index=0)
        text_year = f'{min_year} - {max_year}'
    show_genres = st.multiselect('Genres', st.session_state.all_genres, default=None)
    if len(show_genres) > 0:
        subgenres = []
        for genre in show_genres:
            subgenres += st.session_state.genres_payload[genre]
        show_subgenres = st.multiselect('Subgenres', subgenres, default=None)
    else:
        show_subgenres = None
    show_publications = st.multiselect('Publications', st.session_state.all_publications, default=None)
    if len(show_publications) > 0:
        lists = []
        for publication in show_publications:
            lists += st.session_state.publications_payload[publication]
        lists = sorted(lists)
        show_lists = st.multiselect('Lists', lists, default=None)
    else:
        show_publications = None
        show_lists = None
relevant_albums = get_relevant_albums(min_year, max_year, show_genres, show_subgenres, show_publications, show_lists)
with st.sidebar:
    if 'spotify' in st.session_state:
        with st.expander('Playback Settings', expanded=False):
            random_order = st.radio('Shuffle Playback?', [True, False], help='Shuffle order of albums played')
            weight_albums = st.radio('Weight Albums?', [True, False], help='Higher-ranked albums are more likely to be played')
            weight_tracks = st.radio('Weight Tracks?', [True, False], index=1, help='More popular songs are more likely to be played')
            repeat_albums = st.radio('Repeat Albums?', [True, False], help='Albums are more likely to be repeated')
            album_limit = st.selectbox('Album Limit?', [50,100,250,500], index=1, help='Number of albums to include in pool for potential playlist')
        play_songs = st.button('Play songs via Spotify', help="Play songs based on above parameters")
        create_playlist = st.button('Export playlist to Spotify', help="Export current playlist to Spotify")
        col1, col2, col3 = st.columns(3)
        with col1:
            previous_song = st.button('\u23EA')
        with col2:
            resume_song = st.button('\u25B6\u23F8')
        with col3:
            next_song = st.button('\u23E9')
        if create_playlist:
            if 'track_uris' in st.session_state:
                tracks = st.session_state.track_uris
            else:
                tracks = return_tracks(relevant_albums, 
                                        random_order=random_order,
                                        replace_albums=repeat_albums, 
                                        weight_albums=weight_albums, 
                                        weight_tracks=weight_tracks,
                                        album_limit=album_limit)
            text_genre = get_genre_for_playlist(show_genres, show_subgenres)
            text_publication = get_publication_for_playlist(show_publications)
            spotify_create_playlist(tracks=tracks,
                                    year=text_year, 
                                    genre=text_genre, 
                                    publication=text_publication, 
                                    )
        if play_songs:
            st.session_state.track_info = return_tracks(relevant_albums, 
                                                        random_order=random_order, 
                                                        replace_albums=repeat_albums, 
                                                        weight_albums=weight_albums, 
                                                        weight_tracks=weight_tracks,
                                                        album_limit=album_limit)
            st.session_state.track_uris = ['spotify:track:' + i for i in list(st.session_state.track_info.index)]
            spotipy_start_playback(uris=st.session_state.track_uris)
            st.session_state.playlist_id = None
        if resume_song:
            x = spotipy_current_playback()
            is_playing = False
            if x:
                is_playing = x['is_playing']
            if is_playing:
                spotipy_pause_playback()
            else:
                spotipy_start_playback()
        if previous_song:
            spotipy_previous_track()
        if next_song:
            spotipy_next_track()
        if 'spotipy_error' in st.session_state:
            if st.session_state.spotipy_error:
                st.write(st.session_state.spotipy_error)
show_albums(relevant_albums, 0, 50, show_subgenres)
spotify_player()