import streamlit as st
from spotipy_helper import *
from apple_music_helper import *
from _utils import *

st.set_page_config('Top Albums', layout="wide")

page_header()

# spotipy_setup()

apple_music_setup()

# st.write(st.session_state)