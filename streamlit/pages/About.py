import streamlit as st
from _utils import *

st.set_page_config('Top Albums', layout="wide")

page_header()

st.subheader('Purpose')

st.markdown('''**TopMusic** is a site that helps you find new music. It leverages dozens of of year-end lists to give you music recommendations based on an artist, genre, or year. 
            
Currently it features over **70,000 tracks** from over **6,000 albums** released since 2000. It is updated regularly to add new lists and new albums.''')

st.subheader('How to Use')

st.markdown('''There are two main pages here. The **Radio** page lets you start a radio based on a genre or artist, while the **Top Albums** page lets you start a radio based on year-end lists from different publications. From either page, You can create Apple Music playlists based on the albums featured.
            
TopMusic is optimized for desktop. For a mobile experience, we recommend [downloading](https://apps.apple.com/us/app/topmusicapp/id6746345416) the TopMusic app for iOS.''')

st.subheader('Apple Music')

st.markdown('''TopMusic is integrated with Apple Music, letting you create playlists based upon your custom radio. Have fun! **Note that you must have an Apple Music subscription to create playlists.**
''')

st.subheader('Tech')

st.markdown('''I'll be adding a design doc soon to detail how the app works. At a high level, it uses Streamlit as a frontend and FastAPI as a backend. 
            
Recommendations are made by finding similar tracks based on audio features, genre, and list placement.
            
Apple Music credentials are used in the frontend via OAuth authentication to create playlists. No credentials or information are stored outside of the web session.''')