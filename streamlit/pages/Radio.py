import datetime
import streamlit as st
from callbacks import *
from query_commands import *
from spotipy_helper import *

st.set_page_config('Radio', layout="wide")

feature_list = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']

initiate_genres()
initiate_artists()

spotipy_setup()

if 'available_albums' not in st.session_state:
    st.session_state.available_albums = ['All']
if 'available_songs' not in st.session_state:
    st.session_state.available_songs = ['All']

with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('[About](https://www.evanagovino.com/posts/why-does-topmusic-exist)')
    with col2:
        st.markdown('[Disconnect](https://topmusic.page)')
    radio_type = st.selectbox('Choose a Radio Type',
                              ['Genre', 'Artist'],
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
                                range(2010,2024), 
                                index=0,
                                key='min_year')
        max_year = st.selectbox('Last Year', 
                                list(range(2010,2024))[::-1], 
                                index=0,
                                key='max_year')
        show_years = list(range(min_year, max_year + 1))
        text_year = f'{min_year} - {max_year}'
    else:
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
st.header('TopMusic')
st.subheader('A new way to discover music.')
st.subheader('Pick a Genre or Artist to Start Your Radio')
if 'genre_selection' in st.session_state:
    st.write('Genre:', st.session_state.genre_selection)
if 'subgenre_selection' in st.session_state:
    st.write('Subgenre:', st.session_state.subgenre_selection)
# Show selected Artist + Album + Song
if 'artist_selection' in st.session_state:
    st.write('Artist:', st.session_state.artist_selection)
if 'artist_id' in st.session_state:
    st.write('Artist ID:', st.session_state.artist_id)
if 'album_selection' in st.session_state:
    st.write('Album:', st.session_state.album_selection)
if 'album_id' in st.session_state:
    if st.session_state.album_id != 'None':
        st.write('Album ID:', st.session_state.album_id)
if 'song_selection' in st.session_state:
    st.write('Song:', st.session_state.song_selection)
if 'track_id' in st.session_state:
    st.write('Track ID:', st.session_state.track_id)
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
else:
    display = None
playback_settings = st.expander('Playback Settings', expanded=False)
with playback_settings:
    model_features = st.multiselect(
                'Song features to include in model',
                feature_list,
                default=feature_list,
                key='model_features',
                # on_change=features_callback
                )
    restrict_genre = st.checkbox('Restrict To Same Genre', key='restrict_genre', value=True)
    unskew_features = st.checkbox('Unskew Features', value=True, key='unskew_features')
    duration_min_minute = st.checkbox('Only return songs longer than 1 Minute', value=True, key='duration_min_minute')
with st.sidebar:
    play_songs = st.button('Play songs via Spotify', 
                           help="Play songs based on above parameters",
                           )
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
            radio_callback()
            st.session_state.track_uris = ['spotify:track:' + i for i in list(st.session_state.track_info.index)]
            tracks = st.session_state.track_uris
        spotify_create_playlist(tracks=tracks,
                                year="Test", 
                                genre="Test", 
                                publication="Test", 
                                )
    if play_songs:
        radio_callback()
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
    # if 'spotipy_error' in st.session_state:
    #     st.write(st.session_state.spotipy_error)
    # if st.session_state.playlist_id:
    #     playlist_link = f'https://open.spotify.com/playlist/{st.session_state.playlist_id}'
    #     link = f'[Click here to see your created playlist]({playlist_link})'
    #     st.markdown(link, unsafe_allow_html=True)

spotify_player()

display_songs = st.expander('Display Songs', expanded=False)
with display_songs:
    if 'track_info' in st.session_state:
        st.table(st.session_state.track_info)
    else:
        st.write('No songs to display! Perhaps you need to start a radio?')

st.subheader('Recommended Albums')
if 'track_info' in st.session_state:
    show_albums_two(st.session_state.track_info)