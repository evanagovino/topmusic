import streamlit as st
from _utils import *

st.set_page_config('Albums of the Year', layout="wide")

st.header('TopMusic')
st.subheader('A new way to discover music.')

for item in st.session_state:
    print(item, st.session_state[item])