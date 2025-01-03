import streamlit as st
import numpy as np

def normalize_weights(weights):
    weight_sum = np.sum(weights)
    if weight_sum > 0:
        return [i/weight_sum for i in weights]
    else:
        return [1/len(weights) for i in weights]
    
def reweight_list(weights, top_multiplier=5):
    result = [(i - np.min(weights)) / (np.max(weights) - np.min(weights)) * ((np.min(weights) * top_multiplier) - np.min(weights)) + np.min(weights) for i in weights]
    return normalize_weights(result)
    
def sort_list(lst):
    return ['All'] + sorted(lst)

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
    st.subheader('A new way to discover music.')
        