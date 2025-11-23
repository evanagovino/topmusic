import datetime
import streamlit as st
from callbacks import *
from query_commands import *
from apple_music_helper import *

st.set_page_config('Top Albums', layout="wide")

page_header()

init_time = datetime.datetime.now()

initiate_genres()
initiate_artists()
initiate_publications()
initiate_moods()

st.session_state.current_session_status = get_session_status()

if 'track_info' in st.session_state:
    del st.session_state['track_info']

with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('[About](https://www.evanagovino.com/posts/why-does-topmusic-exist)')
    with col2:
        st.markdown('[Disconnect](https://topmusic.lol)') # Still Need to Update This
    year_selection = st.selectbox('One or Multiple Years?', ['One Year', 'Multiple Years'], index=0)
    if year_selection == 'One Year':
        show_years = st.selectbox('Year', list(range(2000,2026))[::-1], index=0)
        min_year = show_years
        max_year = show_years
        text_year = show_years
    else:
        col1, col2 = st.columns(2)
        with col1:
            min_year = st.selectbox('First Year', range(2000,2026), index=0)
        with col2:
            max_year = st.selectbox('Last Year', list(range(2000,2026))[::-1], index=0)
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
    st.session_state.all_lists = get_relevant_lists(min_year, max_year, show_genres, show_subgenres, show_publications)
    show_lists = st.multiselect('Lists', st.session_state.all_lists, default=None)
    show_moods = st.multiselect('Moods', st.session_state.all_moods, default=None)
relevant_albums = get_relevant_albums(min_year, max_year, show_genres, show_subgenres, show_publications, show_lists, show_moods)
with st.sidebar:
    if st.session_state.current_session_status:
        with st.expander('Playback Settings', expanded=False):
            random_order = st.radio('Shuffle Playback?', [True, False], help='Shuffle order of albums played')
            weight_albums = st.radio('Weight Albums?', [True, False], help='Higher-ranked albums are more likely to be played')
            weight_tracks = st.radio('Weight Tracks?', [True, False], index=1, help='More popular songs are more likely to be played')
            repeat_albums = st.radio('Repeat Albums?', [True, False], help='Albums are more likely to be repeated')
            album_limit = st.selectbox('Album Limit?', [50,100,250,500], index=1, help='Number of albums to include in pool for potential playlist')
        create_playlist = st.button('Export playlist to Apple Music', help="Export current playlist to Apple Music")
        if create_playlist:
            st.session_state.track_info = return_tracks(relevant_albums, 
                                                        random_order=random_order,
                                                        replace_albums=repeat_albums, 
                                                        weight_albums=weight_albums, 
                                                        weight_tracks=weight_tracks,
                                                        album_limit=album_limit
                                                        )
            st.session_state.track_uris = [i for i in list(st.session_state.track_info['track_id'])]
            text_genre = get_genre_for_playlist(show_genres, 
                                                show_subgenres)
            text_publication = get_publication_for_playlist(show_publications)
            playlist_name = f'{text_year}'
            if text_genre != '':
                playlist_name += f' {text_genre}'
            if text_publication != '':
                playlist_name += f' {text_publication}'
            apple_music_create_playlist(tracks=st.session_state.track_uris,
                                        playlist_name=playlist_name
                                        )
show_albums(relevant_albums, 0, 50, show_subgenres)
apple_music_player()