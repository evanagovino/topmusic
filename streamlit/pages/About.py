import streamlit as st
from _utils import *

st.set_page_config('Top Albums', layout="wide")

page_header()

st.subheader('Purpose')

st.markdown('''**TopMusic** is a site that helps you find new music. It leverages track metadata from Spotify and dozens of of year-end lists to give you recommendations based on an artist, genre, or year. 
            
Currently it features over **45,000 tracks** from over **4,500 albums** released since 2010. It is updated regularly to add new lists and new albums.''')

st.subheader('How to Use')

st.markdown('''There are two main pages here. The **Radio** page lets you start a radio based on a genre or artist, while the **Top Albums** page lets you start a radio based on year-end lists from different publications.

You can stream these albums in the browser or create Spotify playlists based the albums featured. For example, [here](https://open.spotify.com/playlist/7bvl1VUsqzBesnHMAWxmVP?si=6fe999d3b4024d21&nd=1&dlsi=8ca9dd7704ea4c9f) is a playlist of some of the best of jazz from 2022.
            
TopMusic should work on any browser, but is optimized for desktop.''')

st.subheader('Spotify')

st.markdown('''TopMusic is integrated with Spotify. Note that triggering playback will start playback on your Spotify player. There is no player in the browser. It is typically helpful to press play on Spotify before starting playback on the page.

You must have Spotify Premium to trigger playback, but you can create a playlist as long as you have a Spotify account.
''')

st.subheader('Tech')

st.markdown('''I'll be adding a design doc soon to detail how the app works. At a high level, it uses Streamlit as a frontend and FastAPI as a backend. 
            
Recommendations are made by finding similar tracks based on audio features, genre, and list placement.
            
Spotify credentials are used in the frontend via OAuth authentication to trigger playback and create playlists. No credentials or information are stored outside of the web session.''')