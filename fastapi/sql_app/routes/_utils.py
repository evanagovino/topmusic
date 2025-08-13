from .. import crud
from ..database import get_db
from fastapi import HTTPException, Query, Depends
import numpy as np
import pandas as pd
from sklearn.metrics import pairwise
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session
import datetime
import json

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
    """
    Unpack a payload of albums into a dataframe, given a weight of total points vs. points pct to order them by
    """    
    x = {'albums': {}}
    for position, value in enumerate(db_albums):
        x['albums'][value.album_uri] = {'artist': value.artist,
                                        'album_id': value.album_uri,
                                        'album_key': value.album_key,
                                        'album_url': value.album_url,
                                        'album_deeplink': value.spotify_deeplink,
                                        'image_url': value.image_url,
                                        'album': value.album,
                                        'genre': value.genre,
                                        'subgenre': value.subgenre,
                                        'year': value.year,
                                        'points': value[10],
                                        'total_points': value[11],
                                        'points_pct': value[10] / value[11]
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

def unpack_albums_new(db_albums, points_weight):
    """
    Unpack a payload of albums into a dataframe, given a weight of total points vs. points pct to order them by
    """    
    x = {'albums': {}}
    for position, value in enumerate(db_albums):
        x['albums'][value.album_key] = {'year': value.year,
                                        'album_key': value.album_key,
                                        'artist': value.artist,
                                        'album': value.album,
                                        'genre': value.genre,
                                        'subgenre': value.subgenre,
                                        'apple_music_album_id': value.apple_music_album_id,
                                        'apple_music_album_url': value.apple_music_album_url,
                                        'spotify_album_uri': value.spotify_album_uri,
                                        'image_url': value.image_url,
                                        'points': value[10],
                                        'total_points': value[11],
                                        'points_pct': value[10] / value[11]
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
    """
    Unpack a payload of genres into a dataframe, given a set of features.
    """
    x = {'genres': {}}
    for position, value in enumerate(db_genres):
        feature_clean_list = []
        x['genres'][value.genre] = {}
        for feature in features:
            feature_clean = feature.split('_')[0]
            feature_clean_list.append(feature_clean)
            x['genres'][value.genre][feature_clean] = getattr(value, feature)
    genre_df = pd.DataFrame.from_dict(x['genres'], orient='index')
    return genre_df

def unpack_artists(db_artists, features):
    """
    Unpack a payload of artists into a dataframe, given a set of features.
    """
    x = {'artists': {}}
    for position, value in enumerate(db_artists):
        feature_clean_list = []
        x['artists'][value.artist_id] = {}
        for feature in features:
            feature_clean = feature.split('_')[0]
            feature_clean_list.append(feature_clean)
            x['artists'][value.artist_id][feature_clean] = getattr(value, feature)
    artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
    return artist_df

def generic_unpack(db, features, dictionary_name, id_column) -> pd.DataFrame:
    x = {dictionary_name: {}}
    for position, value in enumerate(db):
        x[dictionary_name][getattr(value, id_column)] = {}
        for feature in features:
            feature_clean = feature.split('_')[0]
            x[dictionary_name][getattr(value, id_column)][feature_clean] = getattr(value, feature)
    return pd.DataFrame.from_dict(x[dictionary_name], orient='index')


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
    """
    Return cosine similarities for a given input given a dataframe.
    """
    distances = pairwise.cosine_similarity(matrix_values)
    distance_results = np.sort(distances[artist_location])[::-1]
    artist_results = artist_df.index[np.argsort(distances[artist_location])][::-1]
    x = {'artists': {}}
    for position, value in enumerate(artist_results):
        x['artists'][value] = float(distance_results[position])
    return x

def get_album_cosine_similarities(album_df, album_location, matrix_values):
    """
    Return cosine similarities for a given input given a dataframe.
    """
    distances = pairwise.cosine_similarity(matrix_values)
    distance_results = np.sort(distances[album_location])[::-1]
    album_results = album_df.index[np.argsort(distances[album_location])][::-1]
    x = {'albums': {}}
    for position, value in enumerate(album_results):
        x['albums'][value] = float(distance_results[position])
    return x

def get_euclidean_distances(df, input, dict_name):
    """
    Return euclidean distances for a given input given a dataframe.
    """
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

def pull_relevant_albums(db, 
                         min_year, 
                         max_year, 
                         genre, 
                         subgenre, 
                         publication, 
                         list,
                         points_weight,
                         album_uri_required):
    db_albums = crud.get_relevant_albums(db, 
                                         min_year=min_year, 
                                         max_year=max_year, 
                                         genre=genre, 
                                         subgenre=subgenre, 
                                         publication=publication, 
                                         list=list,
                                         album_uri_required=album_uri_required
                                         )
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    return unpack_albums(db_albums, points_weight)

def pull_relevant_albums_new(db, 
                             min_year, 
                             max_year, 
                             genre, 
                             subgenre, 
                             publication, 
                             list,
                             points_weight,
                             album_uri_required):
    db_albums = crud.get_relevant_albums_new(db, 
                                             min_year=min_year, 
                                             max_year=max_year, 
                                             genre=genre, 
                                             subgenre=subgenre, 
                                             publication=publication, 
                                             list=list,
                                             album_uri_required=album_uri_required
                                             )
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    return unpack_albums_new(db_albums, points_weight)
    

def _get_tracks_for_albums(db, 
                           album_ids, 
                           min_duration: int = 60000,
                           max_duration: int = 600000
                           ):
    db_album = crud.get_tracks_for_albums(db, 
                                          album_ids=album_ids, 
                                          min_duration=min_duration,
                                          max_duration=max_duration
                                          )
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    x = {'albums': {}}
    for position, value in enumerate(db_album):
        track_info = {'album_id': value[0],
                     'track_name': value[1],
                     'track_id': value[2],
                     'popularity': value[3],
                     'artist': value[4],
                     'album_name': value[5],
                     'genre': value[6],
                     'subgenre': value[7],
                     'year': value[8],
                     'image_url': value[9],
                     'album_url': value[10],
                     'track_id_spotify_uri': f'spotify:track:{value[2]}'
                     }
        if track_info['album_id'] not in x['albums']:
            x['albums'][track_info['album_id']] = []
        x['albums'][track_info['album_id']].append(track_info)
    return x

def _get_tracks_for_albums_new(db, 
                               album_keys, 
                               min_duration: int = 60000,
                               max_duration: int = 600000
                               ):
    db_album = crud.get_tracks_for_albums_new(db, 
                                              album_keys=album_keys, 
                                              min_duration=min_duration,
                                              max_duration=max_duration
                                              )
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    x = {'albums': {}}
    for position, value in enumerate(db_album):
        track_info = {'album_key': value.album_key,
                     'track_name': value.apple_music_track_name,
                     'track_id': value.apple_music_track_id,
                     'popularity': value.track_popularity,
                     'artist': value.artist,
                     'album_name': value.album,
                     'genre': value.genre,
                     'subgenre': value.subgenre,
                     'year': value.year,
                     'image_url': value.image_url,
                     'album_url': value.apple_music_album_url,
                     'track_id_spotify_uri': f'spotify:track:{value.spotify_album_uri}'
                     }
        if track_info['album_key'] not in x['albums']:
            x['albums'][track_info['album_key']] = []
        x['albums'][track_info['album_key']].append(track_info)
    return x

def return_tracks(db,
                  album_uris,
                  weighted_rank, 
                  random_order=True, 
                  track_length=50, 
                  replace_albums=True, 
                  weight_albums=True, 
                  weight_tracks=True,
                  album_limit=500,
                  max_songs_per_album=3
                  ):
    # Reweight Ranks
    album_uris = album_uris[:album_limit]
    weighted_rank = weighted_rank[:album_limit]
    weighted_rank = reweight_list(weighted_rank)
    album_choice = {}
    if replace_albums == False:
        request_length = min(track_length, len(album_uris))
        album_results = np.random.choice(album_uris, 
                                         replace=replace_albums, 
                                         size=request_length, 
                                         p=weighted_rank)
        for album in album_results:
            album_choice[album] = 1
    else:
        max_occurrence_count = max(max_songs_per_album, (track_length // len(album_uris)) + 1)
        # sloppy custom way to limit random selection so top albums aren't overpulled in smaller pools
        for i in range(track_length):
            result = np.random.choice(album_uris, 
                                      replace=True, 
                                      size=1, 
                                      p=weighted_rank)[0]
            if result not in album_choice:
                album_choice[result] = 1
            else:
                album_choice[result] += 1
            if album_choice[result] >= max_occurrence_count:
                item_index = album_uris.index(result)
                del album_uris[item_index]
                del weighted_rank[item_index]
                weighted_rank = normalize_weights(weighted_rank)
    track_results = _get_tracks_for_albums(db=db, album_ids=[i for i in album_choice])
    final_tracks = []
    for album in album_choice:
        if album not in track_results['albums']:
            track_results['albums'][album] = []
        track_request_size = min(album_choice[album], len(track_results['albums'][album]))
        if len(track_results['albums'][album]) > 0:
            if weight_tracks:
                track_popularity = [i['popularity'] for i in track_results['albums'][album]]
            else:
                track_popularity = [1 for i in track_results['albums'][album]]
            track_popularity = reweight_list(track_popularity)
            tracks_to_add = np.random.choice(track_results['albums'][album], 
                                            size=track_request_size, 
                                            replace=False,
                                            p=track_popularity)
            for track in tracks_to_add:
                final_tracks.append(track)
    return final_tracks

def return_tracks_new(db,
                     album_uris,
                     weighted_rank, 
                     random_order=True, 
                     track_length=50, 
                     replace_albums=True, 
                     weight_albums=True, 
                     weight_tracks=True,
                     album_limit=500,
                     max_songs_per_album=3
                     ):
    # Reweight Ranks
    album_uris = album_uris[:album_limit]
    weighted_rank = weighted_rank[:album_limit]
    weighted_rank = reweight_list(weighted_rank)
    album_choice = {}
    if replace_albums == False:
        request_length = min(track_length, len(album_uris))
        album_results = np.random.choice(album_uris, 
                                         replace=replace_albums, 
                                         size=request_length, 
                                         p=weighted_rank)
        for album in album_results:
            album_choice[album] = 1
    else:
        max_occurrence_count = max(max_songs_per_album, (track_length // len(album_uris)) + 1)
        # sloppy custom way to limit random selection so top albums aren't overpulled in smaller pools
        for i in range(track_length):
            result = np.random.choice(album_uris, 
                                      replace=True, 
                                      size=1, 
                                      p=weighted_rank)[0]
            if result not in album_choice:
                album_choice[result] = 1
            else:
                album_choice[result] += 1
            if album_choice[result] >= max_occurrence_count:
                item_index = album_uris.index(result)
                del album_uris[item_index]
                del weighted_rank[item_index]
                weighted_rank = normalize_weights(weighted_rank)
    track_results = _get_tracks_for_albums_new(db=db, album_keys=[i for i in album_choice])
    final_tracks = []
    for album in album_choice:
        if album not in track_results['albums']:
            track_results['albums'][album] = []
        track_request_size = min(album_choice[album], len(track_results['albums'][album]))
        if len(track_results['albums'][album]) > 0:
            if weight_tracks:
                track_popularity = [i['popularity'] for i in track_results['albums'][album]]
            else:
                track_popularity = [1 for i in track_results['albums'][album]]
            track_popularity = reweight_list(track_popularity)
            tracks_to_add = np.random.choice(track_results['albums'][album], 
                                            size=track_request_size, 
                                            replace=False,
                                            p=track_popularity)
            for track in tracks_to_add:
                final_tracks.append(track)
    return final_tracks

def _get_similar_genres(genre: str, 
                        features: list,
                        unskew_features: bool,
                        db
                        ):
    features = unskew_features_function(features, unskew_features)
    db_genres = crud.get_similar_genres(db)
    genre_df = unpack_genres(db_genres, features)
    if genre not in genre_df.index:
        raise HTTPException(status_code=404, detail="Genre not found")
    # x = get_genre_similarities(genre_df, genre)
    return get_euclidean_distances(df=genre_df,
                                   input=genre,
                                   dict_name='genres'
                                   )

def _get_similar_artists_by_track_details(artist_id: str,
                                         features: list,
                                         unskew_features: bool,
                                         db
                                         ):
    features = unskew_features_function(features, unskew_features)
    db_artists = crud.get_artist_track_details(db)
    artist_df = unpack_artists(db_artists, features)
    if artist_id not in artist_df.index:
        raise HTTPException(status_code=404, detail="Artist not found")
    # x = get_artist_similarities(artist_df, artist_id)
    return get_euclidean_distances(df=artist_df,
                                   input=artist_id,
                                   dict_name='artists'
                                   )

def _get_similar_albums_by_track_details(album_id: str,
                                         features: list,
                                         restrict_genre: bool,
                                         unskew_features: bool,
                                         db
                                         ):
    features = unskew_features_function(features, unskew_features)
    db_album_data = crud.get_tracks_for_album(db, album_id=album_id)
    if len(db_album_data) == 0:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    genre = db_album_data[0].genre
    if restrict_genre:
        db_albums = crud.get_album_track_details(db, genre=genre)
    else:
        db_albums = crud.get_album_track_details(db)
    album_df = generic_unpack(db_albums, features, 'albums', 'album_id')
    return get_euclidean_distances(df=album_df,
                                   input=album_id,
                                   dict_name='albums'
                                   )

def _get_similar_artists_by_genre(artist_id: str,
                                  db
                                  ):
    db_albums = crud.get_similar_artists_by_genre(db)
    x = {'artists': {}}
    for position, value in enumerate(db_albums):
        x['artists'][value.artist_id] = value.genre_data
    artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
    try:
        artist_location = np.where(artist_df.index == artist_id)[0][0]
    except:
        raise HTTPException(status_code=404, detail="No artists that match criteria")
    matrix_values = artist_df.apply(pd.Series)
    x = get_artist_cosine_similarities(artist_df, artist_location, matrix_values)
    return x

def _get_similar_artists_by_publication(artist_id: str,
                                        db
                                        ):
    db_albums = crud.get_similar_artists_by_publication(db)
    x = {'artists': {}}
    for position, value in enumerate(db_albums):
        x['artists'][value.artist_id] = value.publication_data
    artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
    try:
        artist_location = np.where(artist_df.index == artist_id)[0][0]
    except:
        raise HTTPException(status_code=404, detail="No artists that match criteria")
    matrix_values = artist_df.apply(pd.Series)
    return get_artist_cosine_similarities(artist_df, artist_location, matrix_values)

def _get_similar_albums_by_publication(album_id: str,
                                        restrict_genre: bool,
                                        db
                                        ):
    db_album_data = crud.get_tracks_for_album(db, album_id=album_id)
    if len(db_album_data) == 0:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    genre = db_album_data[0].genre
    if restrict_genre:
        db_albums = crud.get_similar_albums_by_publication(db, genre=genre)
    else:
        db_albums = crud.get_similar_albums_by_publication(db)
    x = {'albums': {}}
    for position, value in enumerate(db_albums):
        x['albums'][value.album_id] = value.publication_data
    album_df = pd.DataFrame.from_dict(x['albums'], orient='index')
    try:
        album_location = np.where(album_df.index == album_id)[0][0]
    except:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    matrix_values = album_df.apply(pd.Series)
    x = get_album_cosine_similarities(album_df, album_location, matrix_values)
    return x

def _get_similar_tracks_by_euclidean_distance(track_id: str,
                                              genre: str,
                                              features: list,
                                              unskew_features: bool,
                                              restrict_genre: bool,
                                              min_duration: int,
                                              max_duration: int,
                                              n_tracks: int,
                                              db
                                              ):
    features = unskew_features_function(features, unskew_features)
    if restrict_genre:
        db_tracks = crud.get_all_tracks_genre(db, 
                                              genre=genre, 
                                              min_duration=min_duration, 
                                              max_duration=max_duration
                                              )
    else:
        db_tracks = crud.get_all_tracks(db, 
                                        min_duration=min_duration, 
                                        max_duration=max_duration
                                        )
    feature_matrix, track_ids, _ = unpack_tracks_new(db_tracks, 
                                                     features
                                                     )
    if track_id not in track_ids:
        raise HTTPException(status_code=404, detail="Track not found")
    similar_tracks, similar_scores = get_track_similarities(track_id=track_id,
                                                            feature_matrix=feature_matrix, 
                                                            track_ids=track_ids,
                                                            n_tracks = n_tracks
                                                            )
    temp_similar_tracks_dict = {}
    for position, value in enumerate(similar_tracks):
        temp_similar_tracks_dict[value] = similar_scores[position]
    similar_track_data = [i for i in db_tracks if i.track_id in similar_tracks]
    _, _, x_similar = unpack_tracks(similar_track_data, 
                                    features
                                    )
    for x in x_similar['tracks']:
        x_similar['tracks'][x]['track_euclidean_distance'] = temp_similar_tracks_dict[x]
    sorted_tracks = sorted(x_similar['tracks'].items(), key=lambda x: x[1]['track_euclidean_distance'])
    x = {'tracks': {}}
    for track in sorted_tracks:
        x['tracks'][track[0]] = track[1]
    return x
    
def _get_similar_tracks(track_id: str, 
                        features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']), 
                        unskew_features: bool = True, 
                        restrict_genre: bool = True, 
                        n_tracks: int = 500,
                        request_length: int = 50,
                        min_duration: int = 60000,
                        max_duration: int = 600000,
                        track_weight: float = 0.1,
                        genre_weight: float = 0.45,
                        artist_weight: float = 0.45,
                        db: Session = Depends(get_db)
                        ):
    #Get Data For Track
    print('Request Start', datetime.datetime.now())
    db_track_data = crud.get_track_data(db, track_id=track_id)
    if len(db_track_data) == 0:
        raise HTTPException(status_code=404, detail="No tracks that match criteria")
    artist_id = db_track_data[0].artist_id
    genre = db_track_data[0].genre
    #Get Similar Tracks
    print('Got Data for Track', datetime.datetime.now())
    x_similar = _get_similar_tracks_by_euclidean_distance(track_id = track_id,
                                                          genre = genre,
                                                          features = features,
                                                          unskew_features = unskew_features,
                                                          restrict_genre = restrict_genre,
                                                          min_duration = min_duration,
                                                          max_duration = max_duration,
                                                          n_tracks = 500,
                                                          db = db
                                                         )
    df = pd.DataFrame.from_dict(x_similar['tracks'], orient='index')
    # print('Got Similar Tracks', datetime.datetime.now())
    # #Get Similar Artists For Track
    # db_albums = crud.get_similar_artists(db)
    # x = {'artists': {}}
    # for position, value in enumerate(db_albums):
    #     x['artists'][value.artist_id] = value.publication_data
    # artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
    # try:
    #     artist_location = np.where(artist_df.index == artist_id)[0][0]
    # except:
    #     raise HTTPException(status_code=404, detail="No artists that match criteria")
    # matrix_values = artist_df.apply(pd.Series)
    # x_artist = get_artist_cosine_similarities(artist_df, artist_location, matrix_values)
    # df_artist = pd.DataFrame.from_dict(x_artist['artists'], orient='index')
    # df_artist.columns = ['artist_similarity_score']
    # df = df.merge(df_artist, left_on='artist_id', right_index=True)
    # print('Got Similar Artists For Track', datetime.datetime.now())
    #Get Similar Genres For Track
    if restrict_genre:
        df['genre_euclidean_distance'] = 0
    else:
        x_genre = _get_similar_genres(genre=genre,
                                      features=features,
                                      unskew_features=unskew_features,
                                      db=db)
        df_genre = pd.DataFrame.from_dict(x_genre['genres'], orient='index')
        df_genre.columns = ['genre_euclidean_distance']
        df = df.merge(df_genre, left_on='genre', right_index=True)
    print('Got Similar Genres For Track', datetime.datetime.now())
    #Get Similar Artists For Track
    x_artist = _get_similar_artists_by_track_details(artist_id=artist_id,
                                                     features=features,
                                                     unskew_features=unskew_features,
                                                     db=db)
    df_artist = pd.DataFrame.from_dict(x_artist['artists'], orient='index')
    df_artist.columns = ['artist_euclidean_distance']
    df = df.merge(df_artist, left_on='artist_id', right_index=True)
    print('Got Similar Artists For Track', datetime.datetime.now())
    df['similarity_score_n'] = (df['track_euclidean_distance'].max() - df['track_euclidean_distance']) / (df['track_euclidean_distance'].max() - df['track_euclidean_distance'].min())
    df['genre_score_n'] = ((df['genre_euclidean_distance'].max() - df['genre_euclidean_distance']) / (df['genre_euclidean_distance'].max() - df['genre_euclidean_distance'].min())).fillna(1)
    df['artist_score_n'] = ((df['artist_euclidean_distance'].max() - df['artist_euclidean_distance']) / (df['artist_euclidean_distance'].max() - df['artist_euclidean_distance'].min())).fillna(1)
    df['weighted_score'] = (df['similarity_score_n'] * track_weight) + (df['artist_score_n'] * artist_weight) + (df['genre_score_n'] * genre_weight)
    # df['weighted_score'] = (df['similarity_score_n'] * 0.7) + (df['genre_score_n'] * 0.3)
    # df['weighted_score'] = (df['similarity_score_n'] * 0.7) + (df['artist_similarity_score'] * 0.15) + (df['genre_score_n'] * 0.15)
    df['artist_rank'] = df.groupby('artist_id')['weighted_score'].rank(ascending=False)
    df = df[df['artist_rank'] <= 5]
    df['reweighted_score'] = normalize_weights(df['weighted_score'])
    df['track_id_spotify_uri'] = [f'spotify:track:{i}' for i in df.index]
    request_length = min(request_length, len(df))
    song_selections = np.random.choice(df.index, 
                                       size=request_length, 
                                       replace=False, 
                                       p=df['reweighted_score']
                                       )
    song_selections = song_selections[np.where(song_selections != track_id)]
    if len(song_selections) == request_length:
        song_selections = song_selections[:request_length]
    df_one = df[df.index == track_id]
    df_two = df[df.index.isin(song_selections)]
    df = pd.concat([df_one, df_two])
    df = df.reset_index()
    df = df.rename(columns={'index': 'track_id'})
    final_x = {}
    final_x['tracks'] = json.loads(df.to_json(orient='records'))
    print('Finish Job', datetime.datetime.now())
    return final_x