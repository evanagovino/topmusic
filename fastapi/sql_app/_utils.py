import numpy as np
import pandas as pd
from sklearn.metrics import pairwise
from decimal import Decimal

def normalize_weights(weights):
    """
    Normalize the weights for a given array so that they all add up to 1
    """
    weight_sum = np.sum(weights)
    if weight_sum > 0:
        return [i/weight_sum for i in weights]
    else:
        return [1/len(weights) for i in weights]
    
def reweight_list(weights, top_multiplier=3):
    """
    Reweight an array of weights so that the top weight is no more than n times greater than the bottom weight
    """
    result = [(i - np.min(weights)) / (np.max(weights) - np.min(weights)) * ((np.min(weights) * top_multiplier) - np.min(weights)) + np.min(weights) for i in weights]
    return normalize_weights(result)
    
def unskew_features_function(features, unskew_features=True):
    """
    Direct a function to point to either the 'clean' vale for a list of features vs. the 'raw' value for a list of features

    Possible candidate for deletion if it's determined that we should universally be using 'cleaned' values
    """
    if unskew_features:
       features = [f'{i}_clean' for i in features]
    else:
       features = [f'{i}_raw' for i in features]
    return features

def unpack_tracks(db_tracks, features):
    x = {'tracks': {}}
    print(type(db_tracks))
    for position, value in enumerate(db_tracks):
        feature_clean_list = []
        x['tracks'][value.track_id] = {}
        for feature in features:
            feature_clean = feature.split('_')[0]
            feature_clean_list.append(feature_clean)
            x['tracks'][value.track_id][feature_clean] = getattr(value, feature)
        x['tracks'][value.track_id]['duration'] = value.duration
        x['tracks'][value.track_id]['track_popularity'] = value.track_popularity
        x['tracks'][value.track_id]['track_name'] = value.track_name
        x['tracks'][value.track_id]['artist'] = value.artist
        x['tracks'][value.track_id]['artist_id'] = value.artist_id
        x['tracks'][value.track_id]['genre'] = value.genre
        x['tracks'][value.track_id]['subgenre'] = value.subgenre
        x['tracks'][value.track_id]['year'] = value.year
        x['tracks'][value.track_id]['image_url'] = value.image_url
        x['tracks'][value.track_id]['album_id'] = value.album_id
        x['tracks'][value.track_id]['album_name'] = value.album_name
        x['tracks'][value.track_id]['album_url'] = value.album_url
    track_df = pd.DataFrame.from_dict(x['tracks'], orient='index')
    track_df = track_df.dropna()
    return track_df, feature_clean_list, x

def unpack_tracks_new(db_tracks, features):
    feature_matrix = np.empty(shape=(len(db_tracks), len(features)))
    for position, value in enumerate(features):
        feature_matrix[:, position] = [getattr(i, value) for i in db_tracks]
    track_ids = [getattr(i, 'track_id') for i in db_tracks]
    genres = [getattr(i, 'genre') for i in db_tracks]
    return feature_matrix, track_ids, genres

def unpack_albums(db_albums, points_weight):    
    x = {'albums': {}}
    for position, value in enumerate(db_albums):
        x['albums'][value.album_uri] = {'artist': value.artist,
                                        'album_id': value.album_uri,
                                        'album_url': value.album_url,
                                        'image_url': value.image_url,
                                        'album': value.album,
                                        'genre': value.genre,
                                        'subgenre': value.subgenre,
                                        'year': value.year,
                                        'points': value[8],
                                        'total_points': value[9],
                                        'points_pct': value[8] / value[9]
                                        }
    total_points = np.sum(x['albums'][i]['points'] for i in x['albums'])
    total_points_pct = np.sum(x['albums'][i]['points_pct'] for i in x['albums'])
    for value in x['albums']:
        x['albums'][value]['weighted_rank'] = float((Decimal(points_weight) * (x['albums'][value]['points'] / total_points)) + ((1 - Decimal(points_weight)) * (x['albums'][value]['points_pct']) / total_points_pct))
    new_dict = {}
    for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True):
        new_dict[value[0]] = value[1]
    x['albums'] = new_dict
    return x

def unpack_genres(db_genres, features):
    x = {'genres': {}}
    for position, value in enumerate(db_genres):
        feature_clean_list = []
        x['genres'][value.genre] = {}
        for feature in features:
            feature_clean = feature.split('_')[0]
            feature_clean_list.append(feature_clean)
            x['genres'][value.genre][feature_clean] = getattr(value, feature)
    genre_df = pd.DataFrame.from_dict(x['genres'], orient='index')
    return genre_df, feature_clean_list, x

def unpack_artists(db_artists, features):
    x = {'artists': {}}
    for position, value in enumerate(db_artists):
        feature_clean_list = []
        x['artists'][value.artist_id] = {}
        for feature in features:
            feature_clean = feature.split('_')[0]
            feature_clean_list.append(feature_clean)
            x['artists'][value.artist_id][feature_clean] = getattr(value, feature)
    artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
    return artist_df, feature_clean_list, x

def get_track_similarities(track_id: str, 
                           feature_matrix, 
                           track_ids: list, 
                           n_tracks: int = 500
                           ):
    """
    Return the n most similar tracks to a given track ID based on the included features
    """
    position = track_ids.index(track_id)
    results = feature_matrix[position, :].reshape(1, feature_matrix.shape[1])
    similarities = pairwise.euclidean_distances(results, feature_matrix)
    similar_track_locations = list(np.argsort(similarities)[0][:n_tracks])
    similar_tracks = [track_ids[i] for i in similar_track_locations]
    similar_scores = list(np.sort(similarities)[0][:n_tracks])
    return similar_tracks, similar_scores

def get_artist_cosine_similarities(artist_df, artist_location, matrix_values):
    distances = pairwise.cosine_similarity(matrix_values)
    distance_results = np.sort(distances[artist_location])[::-1]
    artist_results = artist_df.index[np.argsort(distances[artist_location])][::-1]
    x = {'artists': {}}
    for position, value in enumerate(artist_results):
        x['artists'][value] = float(distance_results[position])
    return x

def get_euclidean_distances(df, input, dict_name):
    matrix_values = df.apply(pd.Series)
    location = np.where(df.index == input)[0][0]
    distances = pairwise.euclidean_distances(matrix_values)
    distance_results = np.sort(distances[location])#[::-1]
    results = df.index[np.argsort(distances[location])]#[::-1]
    print(results)
    x = {dict_name: {}}
    for position, value in enumerate(results):
        x[dict_name][value] = float(distance_results[position])
    return x

# def get_genre_similarities(genre_df, genre):
#     matrix_values = genre_df.apply(pd.Series)
#     genre_location = np.where(genre_df.index == genre)[0][0]
#     distances = pairwise.euclidean_distances(matrix_values)
#     distance_results = np.sort(distances[genre_location])[::-1]
#     genre_results = genre_df.index[np.argsort(distances[genre_location])][::-1]
#     x = {'genres': {}}
#     for position, value in enumerate(genre_results):
#         x['genres'][value] = float(distance_results[position])
#     return x

# def get_artist_similarities(artist_df, artist_id):
#     matrix_values = artist_df.apply(pd.Series)
#     artist_location = np.where(artist_df.index == artist_id)[0][0]
#     distances = pairwise.euclidean_distances(matrix_values)
#     distance_results = np.sort(distances[artist_location])[::-1]
#     artist_results = artist_df.index[np.argsort(distances[artist_location])][::-1]
#     x = {'artists': {}}
#     for position, value in enumerate(artist_results):
#         x['artists'][value] = float(distance_results[position])
#     return x

def get_random_track(db, weight_by_popularity = True):
    '''
    This is currently set up a bit arbitrarily since I'm not sure if I want utils talking to crud
    Assumes that DB has:
    value[1] = 'track_name'
    value[2] = 'track_id'
    value[3] = 'popularity'
    '''
    tracks = {'tracks': []}
    for position, value in enumerate(db):
        tracks['tracks'].append({'track_name': value[1],
                                 'track_id': value[2],
                                 'popularity': value[3]
                                })
    if weight_by_popularity:
        weights = [i['popularity'] for i in tracks['tracks']]
    else:
        weights = [1 for i in tracks['tracks']]
    weights = normalize_weights(weights)
    track_choice = np.random.choice([i['track_id'] for i in tracks['tracks']], p=weights)
    return track_choice