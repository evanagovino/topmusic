import numpy as np
import pandas as pd
from sklearn.metrics import pairwise

def normalize_weights(weights):
    weight_sum = np.sum(weights)
    if weight_sum > 0:
        return [i/weight_sum for i in weights]
    else:
        return [1/len(weights) for i in weights]
    
def unskew_features_function(features, unskew_features=True):
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

def get_track_similarities(track_df, track_id, feature_clean_list, n_tracks, x, restrict_genre=False, min_duration=60000):
    results = track_df[track_df.index == track_id][feature_clean_list].values.reshape(1, len(feature_clean_list))
    track_genre = track_df[track_df.index == track_id]['genre'].values[0]
    if restrict_genre:
        track_df = track_df[track_df['genre'] == track_genre]
    if duration_min > 0:
        track_df = track_df[track_df['duration'] > duration_min]
    similarities = pairwise.euclidean_distances(results, track_df[feature_clean_list].values)
    similar_track_locations = list(np.argsort(similarities)[0][:n_tracks])
    similar_scores = list(np.sort(similarities)[0][:n_tracks])
    for position, value in enumerate(similar_scores):
        x['tracks'][track_df.index[similar_track_locations[position]]]['similarity_score'] = float(value)
    similar_tracks = list(track_df.index[similar_track_locations])
    x_similar = {'tracks': {}}
    for track in similar_tracks:
        x_similar['tracks'][track] = x['tracks'][track]
    return x_similar

def get_track_similarities_new(track_id, genre, feature_matrix, track_ids, genres, restrict_genre=False, n_tracks = 500):
    if restrict_genre:
        indices = [i for i in range(len(genres)) if genres[i] == genre]
        feature_matrix = feature_matrix[indices,:]
        track_ids = [track_ids[i] for i in indices]
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

def get_genre_similarities(genre_df, genre):
    matrix_values = genre_df.apply(pd.Series)
    genre_location = np.where(genre_df.index == genre)[0][0]
    distances = pairwise.euclidean_distances(matrix_values)
    distance_results = np.sort(distances[genre_location])[::-1]
    genre_results = genre_df.index[np.argsort(distances[genre_location])][::-1]
    x = {'genres': {}}
    for position, value in enumerate(genre_results):
        x['genres'][value] = float(distance_results[position])
    return x

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