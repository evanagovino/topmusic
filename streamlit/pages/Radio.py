import datetime
import streamlit as st
from callbacks import *
from query_commands import *
from apple_music_helper import *

st.set_page_config('Top Albums', layout="wide")

page_header()

feature_list = ['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']

initiate_genres()
initiate_artists()
st.session_state.current_session_status = get_session_status()

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
                            #   ['Genre', 'Artist', 'Mood'],
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
                                range(2000,2026), 
                                index=0,
                                key='min_year')
        max_year = st.selectbox('Last Year', 
                                list(range(2000,2026))[::-1], 
                                index=0,
                                key='max_year')
        show_years = list(range(min_year, max_year + 1))
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
                key='model_features'
                )
    restrict_genre = st.checkbox('Restrict To Same Genre', key='restrict_genre', value=True)
    unskew_features = st.checkbox('Unskew Features', value=True, key='unskew_features')
    duration_min_minute = st.checkbox('Only return songs longer than 1 Minute', value=True, key='duration_min_minute')
with st.sidebar:
    if display:
        with st.expander('Playback Settings', expanded=False):
            album_limit = st.selectbox('Album Limit?', [50,100,250,500], index=1, help='Number of albums to include in pool for potential playlist')
        generate = st.button(f'Generate {display} Radio', 
                             help="Generate a radio based on above parameters"
                             )
        if generate:
            st.session_state.generate = True
            radio_callback(album_limit=album_limit)
            st.session_state.track_uris = [i for i in list(st.session_state.track_info['track_id'])]
            if 'playlist_id' in st.session_state:
                del st.session_state['playlist_id']
        if st.session_state.generate:
            if st.session_state.current_session_status:
                create_playlist = st.button('Export playlist to Apple Music', help="Export current playlist to Apple Music")
                if create_playlist:
                    apple_music_create_playlist(tracks=st.session_state.track_uris,
                                                playlist_name=display
                                                )

apple_music_player()

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