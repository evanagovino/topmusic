import datetime
import streamlit as st
from callbacks import *
from query_commands import *
from spotipy_helper import *

st.set_page_config('Top Albums', layout="wide")

page_header()

#feature_list = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
feature_list = ['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']

initiate_genres()
initiate_artists()

spotipy_setup()

if 'available_albums' not in st.session_state:
    st.session_state.available_albums = ['All']
if 'available_songs' not in st.session_state:
    st.session_state.available_songs = ['All']
if 'available_tracks' not in st.session_state:
    st.session_state.available_tracks = ['All']
if 'generate' not in st.session_state:
    st.session_state.generate = False

with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('[About](https://www.evanagovino.com/posts/why-does-topmusic-exist)')
    with col2:
        st.markdown('[Disconnect](https://topmusic.page)')
    radio_type = st.selectbox('Choose a Radio Type',
                              ['Genre', 'Artist', 'Mood'],
                              key='radio_type',
                              on_change=radio_type_callback)
    if st.session_state.radio_type == 'Genre':
        genre = st.selectbox('Choose a Genre',
                            st.session_state.all_genres,
                            key='genre_selection',
                            on_change=genre_callback
                            )
        genre_callback()
        if st.session_state.genre_selection == 'All':
            del st.session_state['genre_selection']
        if 'available_subgenres' not in st.session_state:
            st.session_state.available_subgenres = st.session_state.all_subgenres
        subgenre = st.selectbox('Choose a Subgenre',
                                st.session_state.available_subgenres,
                                key='subgenre_selection')
        if st.session_state.subgenre_selection == 'All':
            del st.session_state['subgenre_selection']
        min_year = st.selectbox('First Year', 
                                range(2010,2025), 
                                index=0,
                                key='min_year')
        max_year = st.selectbox('Last Year', 
                                list(range(2010,2025))[::-1], 
                                index=0,
                                key='max_year')
        show_years = list(range(min_year, max_year + 1))
        text_year = f'{min_year} - {max_year}'
    elif st.session_state.radio_type == 'Artist':
        artist = st.selectbox('Choose an Artist',
                            st.session_state.all_artists,
                            key='artist_selection',
                            on_change=artist_callback
                            )
        if st.session_state.artist_selection == 'All':
            del st.session_state['artist_selection']
            if 'artist_id' in st.session_state:
                del st.session_state['artist_id']
        else:
            if 'artist_id' not in st.session_state:
                artist_callback()
        album = st.selectbox('Choose an Album',
                            st.session_state.available_albums,
                            key='album_selection',
                            on_change=album_callback
                            )
        if st.session_state.album_selection == 'All':
            del st.session_state['album_selection']
            if 'album_id' in st.session_state:
                del st.session_state['album_id']
        else:
            if 'album_id' not in st.session_state:
                album_callback()
        song = st.selectbox('Choose a Song',
                            st.session_state.available_tracks,
                            key='song_selection',
                            on_change=song_callback
                            )
        if st.session_state.song_selection == 'All':
            del st.session_state['song_selection']
            if 'track_id' in st.session_state:
                del st.session_state['track_id']
        else:
            if 'track_id' not in st.session_state:
                song_callback()
    elif st.session_state.radio_type == 'Mood':
        mood = st.selectbox('Choose a Mood',
                            ['Chill','Focus', 'Jazzy Focus', 'Electronic Focus'],
                            key='mood_selection'
                            )
        mood_genres = st.multiselect('Genres', st.session_state.all_genres, default=None, key='mood_genre_selection')


if 'song_selection' in st.session_state:
    display = st.session_state.song_selection
elif 'album_selection' in st.session_state:
    display = st.session_state.album_selection
elif 'artist_id' in st.session_state and 'artist_selection' in st.session_state:
    display = st.session_state.artist_selection
elif 'subgenre_selection' in st.session_state:
    display = st.session_state.subgenre_selection
elif 'genre_selection' in st.session_state:
    display = st.session_state.genre_selection
elif 'mood_selection' in st.session_state:
    display = st.session_state.mood_selection
else:
    display = None
playback_settings = st.expander('Playback Settings', expanded=False)
with playback_settings:
    model_features = st.multiselect(
                'Song features to include in model',
                feature_list,
                default=feature_list,
                key='model_features'
                )
    restrict_genre = st.checkbox('Restrict To Same Genre', key='restrict_genre', value=True)
    unskew_features = st.checkbox('Unskew Features', value=True, key='unskew_features')
    duration_min_minute = st.checkbox('Only return songs longer than 1 Minute', value=True, key='duration_min_minute')
with st.sidebar:
    if display:
        generate = st.button(f'Generate {display} Radio', 
                             help="Generate a radio based on above parameters"
                             )
        if generate:
            st.session_state.generate = True
            radio_callback()
            st.session_state.track_uris = ['spotify:track:' + i for i in list(st.session_state.track_info.index)]
            if 'playlist_id' in st.session_state:
                del st.session_state['playlist_id']
        if st.session_state.generate:
            if 'spotify' in st.session_state:
                    play_songs = st.button('Play songs via Spotify', 
                                        help="Play songs based on above parameters",
                                        )
                    create_playlist = st.button('Export playlist to Spotify', help="Export current playlist to Spotify")
                    if play_songs:
                        spotipy_start_playback(uris=st.session_state.track_uris)
                        st.session_state.playlist_id = None
                    elif create_playlist:
                        if radio_type == 'Genre':
                            spotify_create_playlist(tracks=st.session_state.track_uris,
                                                    year=text_year, 
                                                    genre=display, 
                                                    publication='', 
                                                    )
                        elif radio_type == 'Artist':
                            spotify_create_playlist(tracks=st.session_state.track_uris,
                                                    year='', 
                                                    genre=display, 
                                                    publication='', 
                                                    )
                        elif radio_type == 'Mood':
                            spotify_create_playlist(tracks=st.session_state.track_uris,
                                                    year='', 
                                                    genre=display, 
                                                    publication='', 
                                                    )
    if 'spotify' in st.session_state:
        col1, col2, col3 = st.columns(3)
        with col1:
            previous_song = st.button('\u23EA')
        with col2:
            resume_song = st.button('\u25B6\u23F8')
        with col3:
            next_song = st.button('\u23E9')
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

spotify_player()

display_songs = st.expander('Display Songs', expanded=False)
with display_songs:
    if 'track_info' in st.session_state:
        st.table(st.session_state.track_info)
    else:
        st.write('No songs to display! Perhaps you need to start a radio?')

if display == None:
    st.subheader('Pick a Genre, Artist or Mood to Start Your Radio')

if 'track_info' in st.session_state:
    st.subheader('Recommended Albums')
    show_albums_two(st.session_state.track_info)