from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from sklearn.metrics import pairwise
from scipy import stats
import datetime
import json
from decimal import Decimal

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

# Helper Functions - Utils Functions Using DB
        
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
                     'album_url': value[10]
                     }
        if track_info['album_id'] not in x['albums']:
            x['albums'][track_info['album_id']] = []
        x['albums'][track_info['album_id']].append(track_info)
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

def _get_similar_artists(artist_id: str,
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
    x_artist = _get_similar_artists(artist_id=artist_id,
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

# Endpoints


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

@app.get("/genres_new/", response_model=schemas.GenresList)
def get_distinct_genres_new(db: Session = Depends(get_db)):
    db_genre = crud.get_unique_genres(db)
    x = {'genres': []}
    for i in db_genre:
        genre = i[0]
        subgenre = i[1]
        genre_not_present = True
        for value in x['genres']:
            if value['name'] == genre:
                if subgenre in value['subgenres']:
                    pass
                else:
                    value['subgenres'].append(subgenre)
                genre_not_present = False
                continue
        if genre_not_present:
            x['genres'].append({'name': genre, 'subgenres': [subgenre]})
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

@app.get("/artists_new/", response_model=schemas.ArtistsList)
def get_distinct_artists_new(db: Session = Depends(get_db)):
    db_artist = crud.get_artist_name_ids(db)
    x = {'artists': []}
    for i in db_artist:
        x['artists'].append({'name': i.artist, 'id': i.artist_id})
    return x

@app.get("/artist_id_from_artist_name/", response_model=schemas.ArtistsList)
def get_artist_id_from_artist_name(artist_name: str, db: Session = Depends(get_db)):
    db_artist = crud.get_artist_id_from_name(db, artist_name=artist_name)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    x = {'artists': []}
    for i in db_artist:
        x['artists'].append({'name': i.artist, 'id': i.artist_id})
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
def get_random_track_from_artist(artist_id: str, 
                                 weight_by_popularity: bool = True, 
                                 db: Session = Depends(get_db)
                                 ):
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
def get_random_track_from_album(album_id: str, 
                                weight_by_popularity: bool = True, 
                                db: Session = Depends(get_db)
                                ):
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
    """
    Return a list of relevant albums given a set of inputs

    Returned in dictionary format, used for Streamlit
    """
    return pull_relevant_albums(db=db, 
                                min_year=min_year,
                                max_year=max_year, 
                                genre=genre, 
                                subgenre=subgenre, 
                                publication=publication, 
                                list=list,
                                points_weight=points_weight,
                                album_uri_required=False
                                )

@app.get("/get_relevant_albums_new/", response_model=schemas.AlbumsList)
def get_relevant_albums_new(min_year: int, 
                            max_year: int, 
                            genre: List[str] = Query([None]), 
                            subgenre: List[str] = Query([None]), 
                            publication: List[str] =Query([None]), 
                            list: List[str] = Query([None]), 
                            points_weight: float = 0.5,
                            randomize: bool = False,
                            db: Session = Depends(get_db)
                            ):
    """
    Return a list of relevant albums given a set of inputs

    Returned in list format, used for Flutterflow
    """
    x = pull_relevant_albums(db=db, 
                             min_year=min_year,
                             max_year=max_year, 
                             genre=genre, 
                             subgenre=subgenre, 
                             publication=publication, 
                             list=list,
                             points_weight=points_weight,
                             album_uri_required=False
                             )
    new_dict = []
    for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True):
        new_dict.append(value[1])
    x['albums'] = new_dict
    return x

@app.get("/get_recommended_tracks/", response_model=schemas.TracksList)
def get_recommended_tracks(artist_id: str = None,
                           genre: str = None, 
                           db: Session = Depends(get_db)
                           ):
    """
    Get recommended tracks for either an artist ID input or a genre input.

    If Artist ID is provided, it will be used and all other inputs will be ignored.

    Used for Flutterflow endpoint.
    """
    if artist_id is None and genre is None:
        raise HTTPException(status_code=404, detail="Artist ID or Genre must be provided")
    if artist_id:
        db_artist = crud.get_tracks_for_artist(db, artist_id=artist_id)
        if len(db_artist) == 0:
            raise HTTPException(status_code=404, detail="Artist not found")
        track_id = get_random_track(db_artist)
        return _get_similar_tracks(track_id,
                                   features = ['danceability', 'energy', 'instrumentalness', 'valence', 'tempo'], 
                                   unskew_features = True, 
                                   restrict_genre = True, 
                                   n_tracks = 500,
                                   request_length = 50,
                                   min_duration = 60000,
                                   max_duration = 600000,
                                   db = db
                                   )
    elif genre:
        x = pull_relevant_albums(db, 
                                 min_year=2000, 
                                 max_year=2024, 
                                 genre=[genre], 
                                 subgenre=[''], 
                                 publication=[''], 
                                 list=[''], 
                                 points_weight=0.5,
                                 album_uri_required=True
                                 )
        new_dict = {}
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True):
            new_dict[value[0]] = value[1]
        x['albums'] = new_dict
        album_uris = [x['albums'][i]['album_id'] for i in x['albums']]
        weighted_rank = [x['albums'][i]['weighted_rank'] for i in x['albums']]
        if len(album_uris) == 0 or len(weighted_rank) == 0 or len(album_uris) != len(weighted_rank):
            raise HTTPException(status_code=404, detail="Error Processing Album URIs")
        tracks = return_tracks(db=db,
                               album_uris=album_uris,
                               weighted_rank=weighted_rank,
                               album_limit=100
                               )
        x = {'tracks': []}
        for track in tracks:
            x['tracks'].append(track)
        return x

        


@app.get("/get_similar_artists/{artist_id}", response_model=schemas.Artists)
def get_similar_artists(artist_id: str, 
                        db: Session = Depends(get_db)
                        ):
    """
    Return a list of similar artists to a given artist ID by cosine similarity of placement in music publications

    Not used as an endpoint, but potentially useful in data exploration
    """
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
                       features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']), 
                       unskew_features: bool = True, 
                       db: Session = Depends(get_db)
                       ):
    """
    Return a list of similar genres to a given genre by euclidean distance of musical features

    Not used as an endpoint, but potentially useful in data exploration
    """
    return _get_similar_genres(genre=genre,
                               features=features,
                               unskew_features=unskew_features,
                               db=db)

@app.get("/get_similar_tracks_by_euclidean_distance/{track_id}", response_model=schemas.Tracks)
def get_similar_tracks_by_euclidean_distance(track_id: str, 
                                             features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']), 
                                             unskew_features: bool = True,
                                             restrict_genre: bool = True,
                                             min_duration: int = 60000,
                                             max_duration: int = 600000,
                                             n_tracks: int = 500,
                                             db: Session = Depends(get_db)
                                             ):
    """
    Return a list of similar track IDs to a given track ID by euclidean distance of musical features

    Not used as an endpoint, but potentially useful in data exploration
    """
    db_track_data = crud.get_track_data(db, track_id=track_id)
    if len(db_track_data) == 0:
        raise HTTPException(status_code=404, detail="No tracks that match criteria")
    genre = db_track_data[0].genre
    return _get_similar_tracks_by_euclidean_distance(track_id = track_id,
                                                     genre = genre,
                                                     features = features,
                                                     unskew_features = unskew_features,
                                                     restrict_genre = restrict_genre,
                                                     min_duration = min_duration,
                                                     max_duration = max_duration,
                                                     n_tracks = n_tracks,
                                                     db = db
                                                     )

@app.get("/get_similar_artists_by_track_details/{artist_id}", response_model=schemas.Artists)
def get_similar_artists_by_track_details(artist_id: str, 
                                         features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']), 
                                         unskew_features: bool = True, 
                                         db: Session = Depends(get_db)
                                         ):
    """
    Return a list of similar artist IDs to a given artist ID by euclidean distance of median musical features for each artist

    Not used as an endpoint, but potentially useful in data exploration
    """
    return _get_similar_artists(artist_id=artist_id,
                                features=features,
                                unskew_features=unskew_features,
                                db=db
                                )


@app.get('/get_similar_tracks/{track_id}', response_model=schemas.TracksList)
def get_similar_tracks(track_id: str, 
                       features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']), 
                       unskew_features: bool = True, 
                       restrict_genre: bool = True, 
                       n_tracks: int = 250,
                       request_length: int = 50,
                       min_duration: int = 60000,
                       max_duration: int = 600000,
                       track_weight: float = 0.1,
                       genre_weight: float = 0.45,
                       artist_weight: float = 0.45,
                       db: Session = Depends(get_db)
                       ):
    """
    Return a list of recommended tracks given a single track

    Used as endpoint in Artist Radio in Streamlit
    """
    return _get_similar_tracks(track_id,
                               features = ['danceability', 'energy', 'instrumentalness', 'valence', 'tempo'], 
                               unskew_features = unskew_features, 
                               restrict_genre = restrict_genre, 
                               n_tracks = n_tracks,
                               request_length = request_length,
                               min_duration = min_duration,
                               max_duration = max_duration,
                               track_weight = track_weight,
                               genre_weight = genre_weight,
                               artist_weight = artist_weight,
                               db = db
                               )


@app.get('/get_track_data/{track_id}', response_model=schemas.TrackDetails)
def get_track_data(track_id: str, 
                   db: Session = Depends(get_db)
                   ):
    """
    Return data for a single track.

    Not actually being used anywhere in production, but potentially useful for spot-checking.

    Note this doesn't currently return any audio features of the track.
    """
    db_tracks = crud.get_track_data(db, track_id=track_id)
    if len(db_tracks) == 0:
        raise HTTPException(status_code=404, detail="No tracks that match criteria")
    x = {}
    for position, value in enumerate(db_tracks):
        for feature in ['artist_id', 'track_id','track_name', 'track_popularity', 'genre', 'subgenre', 'year', 'artist', 'image_url']:
            x[feature] = getattr(value, feature)
    return x

@app.get('/get_album_accolades_multiple_albums/', response_model=schemas.Albums)
def get_album_accolades_multiple_albums(album_ids: List[str] = Query([None]),
                                        n_accolades: int = 10,
                                        album_limit: int = 50,
                                        db: Session = Depends(get_db)):
    """
    Return a dictionary of album accolades given a list of album URIs

    Used as endpoint in Top Albums in Streamlit
    """
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
    #print(x['albums'])
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

@app.get('/get_tracks_by_features/', response_model=schemas.Tracks)
def get_tracks_by_features(
                        #    included_genres: List[str] = Query([None]),
                           excluded_genres: List[str] = Query(['']),
                        #    included_subgenres: List[str] = Query([None]),
                           excluded_subgenres: List[str] = Query(['']),
                           excluded_time_signatures: List[int] = Query([0]),
                           min_danceability: float = 0, 
                           max_danceability: float = 1, 
                           min_energy: float = 0, 
                           max_energy: float = 1, 
                           min_speechiness: float = 0, 
                           max_speechiness: float = 1, 
                           min_acousticness: float = 0, 
                           max_acousticness: float = 1, 
                           min_instrumentalness: float = 0, 
                           max_instrumentalness: float = 1, 
                           min_liveness: float = 0, 
                           max_liveness: float = 1, 
                           min_valence: float = 0, 
                           max_valence: float = 1, 
                           min_tempo: float = 50, 
                           max_tempo: float = 170,
                           min_popularity: float = 0,
                           max_popularity: float = 100,
                           track_limit: int = 50,
                           min_duration: int = 60000,
                           max_duration: int = 600000,
                           weight_by_popularity: bool = True,
                           db: Session = Depends(get_db)
                           ):
    """
    Return a list of tracks given a set of feature constraints

    Used in Streamlit for Mood Radio
    """
    db_tracks = crud.get_tracks_by_features(db, 
                                            excluded_genres=excluded_genres,
                                            excluded_subgenres=excluded_subgenres,
                                            excluded_time_signatures=excluded_time_signatures,
                                            min_danceability=min_danceability, 
                                            max_danceability=max_danceability, 
                                            min_energy=min_energy, 
                                            max_energy=max_energy, 
                                            min_speechiness=min_speechiness,
                                            max_speechiness=max_speechiness,
                                            min_acousticness=min_acousticness,
                                            max_acousticness=max_acousticness,
                                            min_instrumentalness=min_instrumentalness,
                                            max_instrumentalness=max_instrumentalness,
                                            min_liveness=min_liveness,
                                            max_liveness=max_liveness,
                                            min_valence=min_valence,
                                            max_valence=max_valence,
                                            min_tempo=min_tempo,
                                            max_tempo=max_tempo,
                                            min_popularity=min_popularity,
                                            max_popularity=max_popularity,
                                            min_duration=min_duration,
                                            max_duration=max_duration
                                            )
    if db_tracks is None:
        raise HTTPException(status_code=404, detail="No tracks that match criteria")
    elif len(db_tracks) == 0:
        raise HTTPException(status_code=404, detail="No tracks that match criteria")
    print('Successfully pulled down data')
    x = {'tracks': {}}
    track_length = min(len(db_tracks), track_limit)
    if weight_by_popularity:
        track_popularity = [i.track_popularity for i in db_tracks]
    else:
        track_popularity = [1 for i in db_tracks]
    track_popularity = reweight_list(track_popularity)
    track_selection = np.random.choice(db_tracks, track_length, replace=False, p=track_popularity)
    features= ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
    features = unskew_features_function(features)
    _, _, tracks = unpack_tracks(track_selection, features)
    return tracks

@app.get("/return_tracks_from_albums/", response_model=schemas.TracksList)
def return_tracks_from_albums(album_uris: List[str] = Query(['']),
                              weighted_rank: bool = True,
                              album_limit: int = 500,
                              track_length: int = 50,
                              shuffle_tracks: bool = True,
                              db: Session = Depends(get_db)):
    """
    Return a list of tracks given a list of albums
    """
    db_albums = crud.get_album_info(db=db,
                                    album_uris=album_uris)
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    x = unpack_albums(db_albums, points_weight=0.5)
    album_uris = [i for i in x['albums']]
    if weighted_rank:
        weighted_ranks = [x['albums'][i]['weighted_rank'] for i in x['albums']]
    else:
        weighted_ranks = [1 for i in x]
    tracks = return_tracks(db,
                           album_uris,
                           weighted_rank=weighted_ranks, 
                           random_order=True, 
                           track_length=track_length, 
                           replace_albums=True, 
                           weight_albums=True, 
                           weight_tracks=True,
                           album_limit=album_limit,
                           max_songs_per_album=3
                          )
    x = {'tracks': []}
    if shuffle_tracks:
        np.random.shuffle(tracks)
    for track in tracks:
        x['tracks'].append(track)
    return x
    

