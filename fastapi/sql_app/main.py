from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from sklearn.metrics import pairwise
from scipy import stats
import datetime
import json

from . import crud, models, schemas
from .database import SessionLocal, engine
from ._utils import *

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/genres/", response_model=schemas.Genres)
def get_distinct_genres(db: Session = Depends(get_db)):
    db_genre = crud.get_unique_genres(db)
    x = {'genres': {}}
    for i in db_genre:
        if i[0] in x['genres']:
            x['genres'][i[0]].append(i[1])
        else:
            x['genres'][i[0]] = [i[1]]
    return x

@app.get("/publications/", response_model=schemas.Publications)
def get_distinct_publications(db: Session = Depends(get_db)):
    db_genre = crud.get_unique_publications(db)
    x = {'publications': {}}
    for i in db_genre:
        if i[0] in x['publications']:
            x['publications'][i[0]].append(i[1])
        else:
            x['publications'][i[0]] = [i[1]]
    return x

@app.get("/artists/", response_model=schemas.Artists)
def get_distinct_artists(db: Session = Depends(get_db)):
    db_artist = crud.get_artist_name_ids(db)
    x = {'artists': {}}
    for i in db_artist:
        x['artists'][i.artist] = i.artist_id
    return x

@app.get("/albums_for_artist/{artist_id}", response_model=schemas.Albums)
def get_albums_for_artist(artist_id: str, db: Session = Depends(get_db)):
    db_album = crud.get_albums_for_artist(db, artist_id=artist_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    x = {'albums': {}}
    for position, value in enumerate(db_album):
        print(position, value, value[0], value[1])
        x['albums'][value[0]] = value[1]
    return x

@app.get("/tracks_for_artist/{artist_id}", response_model=schemas.TracksList)
def get_tracks_for_artist(artist_id: str, db: Session = Depends(get_db)):
    db_artist = crud.get_tracks_for_artist(db, artist_id=artist_id)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    x = {'tracks': []}
    for position, value in enumerate(db_artist):
        track_info = {'album_uri': value[0],
                     'track_name': value[1],
                     'track_id': value[2],
                     'popularity': value[3]
                     }
        x['tracks'].append(track_info)
    return x

@app.get("/tracks_for_album/{album_id}", response_model=schemas.TracksList)
def get_tracks_for_album(album_id: str, db: Session = Depends(get_db)):
    db_album = crud.get_tracks_for_album(db, album_id=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    x = {'tracks': []}
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
                     'album_url': value[10]
                     }
        x['tracks'].append(track_info)
    return x


@app.get("/tracks_for_albums/", response_model=schemas.TracksList)
def get_tracks_for_albums(album_ids: List[str] = Query([None]), db: Session = Depends(get_db)):
    db_album = crud.get_tracks_for_albums(db, album_ids=album_ids)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    x = {'tracks': []}
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
                     'album_url': value[10]
                     }
        x['tracks'].append(track_info)
    return x

@app.get("/random_track_from_artist/{artist_id}", response_model=schemas.Tracks)
def get_random_track_from_artist(artist_id: str, weight_by_popularity: bool = True, db: Session = Depends(get_db)):
    db_artist = crud.get_tracks_for_artist(db, artist_id=artist_id)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    tracks = {'tracks': {}}
    for position, value in enumerate(db_artist):
        tracks['tracks'][value[1]] = {'track_id': value[2],
                                      'popularity': value[3]
                                     }
    if weight_by_popularity:
        weights = [tracks['tracks'][i]['popularity'] for i in tracks['tracks']]
    else:
        weights = [1 for i in tracks['tracks']]
    weights = normalize_weights(weights)
    track_choice = np.random.choice(list(tracks['tracks'].keys()), p=weights)
    return {'tracks': {track_choice: tracks['tracks'][track_choice]}}

@app.get("/random_track_from_album/{album_id}", response_model=schemas.Tracks)
def get_random_track_from_album(album_id: str, weight_by_popularity: bool = True, db: Session = Depends(get_db)):
    db_album = crud.get_tracks_for_album(db, album_id=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    tracks = {'tracks': {}}
    for position, value in enumerate(db_album):
        tracks['tracks'][value[1]] = {
                                      'track_id': value[2],
                                      'popularity': value[3]
                                     }
    if weight_by_popularity:
        weights = [tracks['tracks'][i]['popularity'] for i in tracks['tracks']]
    else:
        weights = [1 for i in tracks['tracks']]
    print('weights', weights)
    weights = normalize_weights(weights)
    track_choice = np.random.choice(list(tracks['tracks'].keys()), p=weights)
    return {'tracks': {track_choice: tracks['tracks'][track_choice]}}

@app.get("/get_similar_tracks/{track_id}", response_model=schemas.Tracks)
def get_similar_tracks(track_id: str, 
                       features: List[str] = Query(['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']), 
                       unskew_features: bool = True, 
                       restrict_genre: bool = True, 
                       n_tracks: int = 500,
                       duration_min: int = 0,
                       db: Session = Depends(get_db)
                       ):
    features = unskew_features_function(features, unskew_features)
    db_tracks = crud.get_all_tracks(db)
    track_df, feature_clean_list, x = unpack_tracks(db_tracks, features)
    if track_id not in track_df.index:
        raise HTTPException(status_code=404, detail="Track not found")
    x_similar = get_track_similarities(track_df, 
                                       track_id, 
                                       feature_clean_list, 
                                       n_tracks,   
                                       x, 
                                       restrict_genre,
                                       duration_min)
    return x_similar

@app.get("/get_relevant_albums/", response_model=schemas.Albums)
def get_relevant_albums(min_year: int, 
                        max_year: int, 
                        genre: List[str] = Query([None]), 
                        subgenre: List[str] = Query([None]), 
                        publication: List[str] =Query([None]), 
                        list: List[str] = Query([None]), 
                        points_weight: float = 0.5, 
                        db: Session = Depends(get_db)
                        ):
    db_albums = crud.get_relevant_albums(db, min_year=min_year, max_year=max_year, genre=genre, subgenre=subgenre, publication=publication, list=list)
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    x = {'albums': {}}
    for position, value in enumerate(db_albums):
        #print(value)
        x['albums'][value.album_uri] = {'artist': value.artist,
                                        'album_id': value.album_uri,
                                        'album_url': value.album_url,
                                        'image_url': value.image_url,
                                        'album': value.album,
                                        'genre': value.genre,
                                        'subgenre': value.subgenre,
                                        'year': value.year,
                                        'points': value[8],
                                        'total_points': value[8],
                                        'points_pct': value[8] / value[9]
                                        }
    album_uris = [i for i in x['albums']]
    points_position = stats.rankdata([x['albums'][i]['points'] for i in x['albums']])
    points_pct_position = stats.rankdata([x['albums'][i]['points_pct'] for i in x['albums']])
    for position, value in enumerate(points_position):
        x['albums'][album_uris[position]]['points_rank'] = float(value)
    for position, value in enumerate(points_pct_position):
        x['albums'][album_uris[position]]['points_pct_rank'] = float(value)
        x['albums'][album_uris[position]]['weighted_rank'] = ((x['albums'][album_uris[position]]['points_rank'] * points_weight) + (x['albums'][album_uris[position]]['points_pct_rank'] * (1 - points_weight)))
    new_dict = {}
    for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True):
        new_dict[value[0]] = value[1]
    x['albums'] = new_dict
    return x

@app.get("/get_similar_artists/{artist_id}", response_model=schemas.Artists)
def get_similar_artists(artist_id: str, 
                        db: Session = Depends(get_db)
                        ):
    db_albums = crud.get_similar_artists(db)
    x = {'artists': {}}
    for position, value in enumerate(db_albums):
        x['artists'][value.artist_id] = value.publication_data
    artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
    try:
        artist_location = np.where(artist_df.index == artist_id)[0][0]
    except:
        raise HTTPException(status_code=404, detail="No artists that match criteria")
    matrix_values = artist_df.apply(pd.Series)
    x = get_artist_cosine_similarities(artist_df, artist_location, matrix_values)
    return x

@app.get("/get_similar_genres/{genre}", response_model=schemas.Genres)
def get_similar_genres(genre: str, 
                       features: List[str] = Query(['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']), 
                       unskew_features: bool = True, 
                       db: Session = Depends(get_db)
                       ):
    features = unskew_features_function(features, unskew_features)
    db_genres = crud.get_similar_genres(db)
    genre_df, feature_clean_list, x = unpack_genres(db_genres, features)
    if genre not in genre_df.index:
        raise HTTPException(status_code=404, detail="Genre not found")
    x = get_genre_similarities(genre_df, genre)
    return x

@app.get('/get_similar_tracks_total/{track_id}', response_model=schemas.Tracks)
def get_total_track_similarity_new(track_id: str, 
                                   features: List[str] = Query(['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']), 
                                   unskew_features: bool = True, 
                                   restrict_genre: bool = True, 
                                   n_tracks: int = 500,
                                   request_length: int = 50,
                                   duration_min: int = 0,
                                   db: Session = Depends(get_db)
                                   ):
    #Get Data For Track
    print('Request Start', datetime.datetime.now())
    db_track_data = crud.get_track_data(db, track_id=track_id)
    if db_track_data is None:
        raise HTTPException(status_code=404, detail="No tracks that match criteria")
    artist_id = db_track_data[0].artist_id
    genre = db_track_data[0].genre
    #Get Similar Tracks
    print('Got Data for Track', datetime.datetime.now())
    features = unskew_features_function(features, unskew_features)
    if restrict_genre:
        db_tracks = crud.get_all_tracks_genre(db, genre=genre)
    else:
        db_tracks = crud.get_all_tracks(db)
    print('All Tracks Call', datetime.datetime.now())
    feature_matrix, track_ids, genres = unpack_tracks_new(db_tracks, features)
    print('Unpacked Tracks', datetime.datetime.now())
    if track_id not in track_ids:
        raise HTTPException(status_code=404, detail="Track not found")
    similar_tracks, similar_scores = get_track_similarities_new(track_id, genre, feature_matrix, track_ids, genres)
    temp_similar_tracks_dict = {}
    for position, value in enumerate(similar_tracks):
        temp_similar_tracks_dict[value] = similar_scores[position]
    similar_track_data = [i for i in db_tracks if i.track_id in similar_tracks]
    track_df, feature_clean_list, x_similar = unpack_tracks(similar_track_data, features)
    for x in x_similar['tracks']:
        x_similar['tracks'][x]['similarity_score'] = temp_similar_tracks_dict[x]
    df = pd.DataFrame.from_dict(x_similar['tracks'], orient='index')
    print('Got Similar Tracks', datetime.datetime.now())
    #Get Similar Artists For Track
    db_albums = crud.get_similar_artists(db)
    x = {'artists': {}}
    for position, value in enumerate(db_albums):
        x['artists'][value.artist_id] = value.publication_data
    artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
    try:
        artist_location = np.where(artist_df.index == artist_id)[0][0]
    except:
        raise HTTPException(status_code=404, detail="No artists that match criteria")
    matrix_values = artist_df.apply(pd.Series)
    x_artist = get_artist_cosine_similarities(artist_df, artist_location, matrix_values)
    df_artist = pd.DataFrame.from_dict(x_artist['artists'], orient='index')
    df_artist.columns = ['artist_similarity_score']
    df = df.merge(df_artist, left_on='artist_id', right_index=True)
    print('Got Similar Artists For Track', datetime.datetime.now())
    #Get Similar Genres For Track
    if restrict_genre:
        df['genre_similarity_score'] = 0
    else:
        db_genres = crud.get_similar_genres(db)
        genre_df, feature_clean_list, x = unpack_genres(db_genres, features)
        if genre not in genre_df.index:
            raise HTTPException(status_code=404, detail="Genre not found")
        x_genre = get_genre_similarities(genre_df, genre)
        df_genre = pd.DataFrame.from_dict(x_genre['genres'], orient='index')
        df_genre.columns = ['genre_similarity_score']
        df = df.merge(df_genre, left_on='genre', right_index=True)
    print('Got Similar Genres For Track', datetime.datetime.now())
    df['similarity_score_n'] = (df['similarity_score'].max() - df['similarity_score']) / (df['similarity_score'].max() - df['similarity_score'].min())
    df['genre_score_n'] = ((df['genre_similarity_score'].max() - df['genre_similarity_score']) / (df['genre_similarity_score'].max() - df['genre_similarity_score'].min())).fillna(1)
    df['weighted_score'] = (df['similarity_score_n'] * 0.7) + (df['artist_similarity_score'] * 0.15) + (df['genre_score_n'] * 0.15)
    df['artist_rank'] = df.groupby('artist_id')['weighted_score'].rank(ascending=False)
    df = df[df['artist_rank'] <= 5]
    df['reweighted_score'] = normalize_weights(df['weighted_score'])
    request_length = min(request_length, len(df))
    song_selections = np.random.choice(df.index, size=request_length, replace=False, p=df['reweighted_score'])
    df = df[df.index.isin(song_selections)]
    final_x = {}
    final_x['tracks'] = json.loads(df.to_json(orient='index'))
    print('Finish Job', datetime.datetime.now())
    return final_x




    


# @app.get("/get_similar_tracks_total/{track_id}", response_model=schemas.Tracks)
# def get_total_track_similarity(track_id: str, 
#                                features: List[str] = Query(['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']), 
#                                unskew_features: bool = True, 
#                                restrict_genre: bool = True, 
#                                n_tracks: int = 500,
#                                request_length: int = 50,
#                                duration_min: int = 0,
#                                db: Session = Depends(get_db)
#                                ):
#     #Get Data For Track
#     print('Request Start', datetime.datetime.now())
#     db_track_data = crud.get_track_data(db, track_id=track_id)
#     if db_track_data is None:
#         raise HTTPException(status_code=404, detail="No tracks that match criteria")
#     x = {}
#     for position, value in enumerate(db_track_data):
#         for feature in ['artist_id', 'track_id','track_name', 'track_popularity', 'genre', 'subgenre', 'year', 'artist', 'image_url']:
#             x[feature] = getattr(value, feature)
#     artist_id = x['artist_id']
#     genre = x['genre']
#     #Get Similar Tracks
#     print('Got Data for Track', datetime.datetime.now())
#     features = unskew_features_function(features, unskew_features)
#     db_tracks = crud.get_all_tracks(db)
#     print('All Tracks Call', datetime.datetime.now())
#     track_df, feature_clean_list, x = unpack_tracks(db_tracks, features)
#     print('Unpacked Tracks', datetime.datetime.now())
#     if track_id not in track_df.index:
#         raise HTTPException(status_code=404, detail="Track not found")
#     x_similar = get_track_similarities(track_df, 
#                                        track_id, 
#                                        feature_clean_list, 
#                                        n_tracks,   
#                                        x, 
#                                        restrict_genre,
#                                        duration_min)
#     df = pd.DataFrame.from_dict(x_similar['tracks'], orient='index')
#     print('Got Similar Tracks', datetime.datetime.now())
#     #Get Similar Artists For Track
#     db_albums = crud.get_similar_artists(db)
#     x = {'artists': {}}
#     for position, value in enumerate(db_albums):
#         x['artists'][value.artist_id] = value.publication_data
#     artist_df = pd.DataFrame.from_dict(x['artists'], orient='index')
#     try:
#         artist_location = np.where(artist_df.index == artist_id)[0][0]
#     except:
#         raise HTTPException(status_code=404, detail="No artists that match criteria")
#     matrix_values = artist_df.apply(pd.Series)
#     x_artist = get_artist_cosine_similarities(artist_df, artist_location, matrix_values)
#     df_artist = pd.DataFrame.from_dict(x_artist['artists'], orient='index')
#     df_artist.columns = ['artist_similarity_score']
#     df = df.merge(df_artist, left_on='artist_id', right_index=True)
#     print('Got Similar Artists For Track', datetime.datetime.now())
#     #Get Similar Genres For Track
#     if restrict_genre:
#         df['genre_similarity_score'] = 0
#     else:
#         db_genres = crud.get_similar_genres(db)
#         genre_df, feature_clean_list, x = unpack_genres(db_genres, features)
#         if genre not in genre_df.index:
#             raise HTTPException(status_code=404, detail="Genre not found")
#         x_genre = get_genre_similarities(genre_df, genre)
#         df_genre = pd.DataFrame.from_dict(x_genre['genres'], orient='index')
#         df_genre.columns = ['genre_similarity_score']
#         df = df.merge(df_genre, left_on='genre', right_index=True)
#     print('Got Similar Genres For Track', datetime.datetime.now())
#     df['similarity_score_n'] = (df['similarity_score'].max() - df['similarity_score']) / (df['similarity_score'].max() - df['similarity_score'].min())
#     df['genre_score_n'] = ((df['genre_similarity_score'].max() - df['genre_similarity_score']) / (df['genre_similarity_score'].max() - df['genre_similarity_score'].min())).fillna(1)
#     df['weighted_score'] = (df['similarity_score_n'] * 0.7) + (df['artist_similarity_score'] * 0.15) + (df['genre_score_n'] * 0.15)
#     df['artist_rank'] = df.groupby('artist_id')['weighted_score'].rank(ascending=False)
#     df = df[df['artist_rank'] <= 5]
#     df['reweighted_score'] = normalize_weights(df['weighted_score'])
#     print(df.shape)
#     request_length = min(request_length, len(df))
#     song_selections = np.random.choice(df.index, size=request_length, replace=False, p=df['reweighted_score'])
#     df = df[df.index.isin(song_selections)]
#     final_x = {}
#     final_x['tracks'] = json.loads(df.to_json(orient='index'))
#     print('Finish Job', datetime.datetime.now())
#     return final_x


@app.get('/get_track_data/{track_id}', response_model=schemas.TrackDetails)
def get_track_data(track_id: str, 
                   db: Session = Depends(get_db)):
    db_tracks = crud.get_track_data(db, track_id=track_id)
    if db_tracks is None:
        raise HTTPException(status_code=404, detail="No tracks that match criteria")
    x = {}
    for position, value in enumerate(db_tracks):
        for feature in ['artist_id', 'track_id','track_name', 'track_popularity', 'genre', 'subgenre', 'year', 'artist', 'image_url']:
            x[feature] = getattr(value, feature)
    return x

@app.get('/get_album_accolades/{album_id}', response_model=schemas.AlbumsList)
def get_album_accolades(album_id: str, 
                        n_accolades: int = 10, 
                        db: Session = Depends(get_db)):
    db_albums = crud.get_album_accolades(db, album_id=album_id)
    # print(len(db_albums))
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    elif len(db_albums) == 0:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    x = {'albums': []}
    for position, value in enumerate(db_albums):
        new_value = {}
        for feature in ['rank', 'points', 'publication', 'list']:
            new_value[feature] = getattr(value, feature)
        x['albums'].append(new_value)
    new_dict = []
    counting_value = 0
    for value in sorted(x['albums'], key=lambda x: x['points'], reverse=True):
        new_dict.append(value)
        counting_value += 1
        if counting_value >= n_accolades:
            break
    x['albums'] = new_dict
    return x

@app.get('/get_album_accolades_multiple_albums/', response_model=schemas.Albums)
def get_album_accolades_multiple_albums(album_ids: List[str] = Query([None]),
                                        n_accolades: int = 10,
                                        album_limit: int = 50,
                                        db: Session = Depends(get_db)):
    db_albums = crud.get_album_accolades_multiple_albums(db, album_ids=album_ids[:album_limit])
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    elif len(db_albums) == 0:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    x = {'albums': {}}
    for position, value in enumerate(db_albums):
        album_uri = getattr(value, 'album_uri')
        if album_uri in x['albums']:
            pass
        else:
            x['albums'][album_uri] = []
        new_value = {}
        for feature in ['rank', 'points', 'publication', 'list']:
            new_value[feature] = getattr(value, feature)
        x['albums'][album_uri].append(new_value)
    print(x['albums'])
    for album in x['albums']:
        new_dict = []
        counting_value = 0
        for value in sorted(x['albums'][album], key=lambda x: x['points'], reverse=True):
            new_dict.append(value)
            counting_value += 1
            if counting_value >= n_accolades:
                break
        x['albums'][album] = new_dict
    return x
    

