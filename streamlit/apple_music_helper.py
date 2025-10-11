import streamlit as st
import requests

fastapi_url = 'http://fastapi:8000'

def get_session_status():
    if 'api_key' in st.session_state:
        auth_url = f'{fastapi_url}/web/get_user_apple_library/'
        response = requests.get(auth_url, headers={'x-api-key': st.session_state.api_key})
        if response.status_code == 200:
            return True
    return False
    

def apple_music_player():
    with st.sidebar:
        if st.session_state.current_session_status:
            st.write('Successfully authenticated with Apple Music')
        else:
            auth_url = 'http://localhost:8008/web/get_apple_music_auth_page/' # note that this URL is currently hard-coded
            link = f'[Authenticate Here to Create Custom Playlists]({auth_url})'
            st.markdown(link, unsafe_allow_html=True)

def apple_music_create_playlist(tracks, playlist_name):
    if st.session_state.current_session_status:
        base_url = f'{fastapi_url}/web/create_apple_music_playlist/'
        base_url += f'?playlist_name={playlist_name}'
        for track in tracks:
            base_url += f'&tracks={track}'
        response = requests.post(base_url, headers={'x-api-key': st.session_state.api_key})
        if response.status_code == 200:
            st.write('Playlist created successfully')
            link = f'[See Your Custom Playlist On Apple Music](music://music.apple.com/us/library/all-playlists/)'
            st.markdown(link, unsafe_allow_html=True)
            link = f'[See Your Custom Playlist On Web](https://music.apple.com/us/library/all-playlists/)'
            st.markdown(link, unsafe_allow_html=True)
        else:
            st.write(response.status_code)

def apple_music_setup():
    query_params = st.query_params
    if "api_key" in query_params and "api_key" not in st.session_state:
        st.session_state.api_key = query_params["api_key"]
        st.query_params.clear()
        st.rerun()
