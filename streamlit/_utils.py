import streamlit as st
import numpy as np

# st.markdown("""
# <style>
# .big-font {
#     font-size:15px;
# }
# </style>
# """, unsafe_allow_html=True)

def normalize_weights(weights):
    weight_sum = np.sum(weights)
    if weight_sum > 0:
        return [i/weight_sum for i in weights]
    else:
        return [1/len(weights) for i in weights]
    
def sort_list(lst):
    lst.append('All')
    lst.sort(key=lambda c: (c!='All',not c.isalnum(), c))
    return lst

def get_genre_for_playlist(show_genres, show_subgenres):
    if show_genres == [] or show_genres is None:
        text_genre = ''
    elif show_subgenres == []:
        list_genre = ','.join(show_genres)
        text_genre = f'- {list_genre}'
    else:
        list_subgenre = ','.join(show_subgenres)
        text_genre = f'- {list_subgenre}'
    return text_genre

def get_publication_for_playlist(show_publications):
    if show_publications == [] or show_publications is None:
        text_publication = ''
    else:
        list_publication = ','.join(show_publications)
        text_publication = f'- {list_publication}'
    return text_publication

def page_header():
    st.header('TopMusic')
    # st.markdown('<p class="big-font">Hello World !!</p>', unsafe_allow_html=True)
    st.subheader('A new way to discover music.')
        