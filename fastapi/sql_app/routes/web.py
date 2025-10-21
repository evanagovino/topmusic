from ..database import get_db
from .. import crud, models, schemas
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter, Request, Header, Response, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ._utils import normalize_weights, reweight_list, unskew_features_function, unpack_tracks, _get_similar_genres, _get_similar_artists_by_track_details, _get_similar_tracks_by_euclidean_distance, _get_similar_tracks, pull_relevant_albums, _get_similar_artists_by_genre, _get_similar_albums_by_track_details, _get_similar_artists_by_publication, _get_similar_albums_by_publication, _get_apple_music_auth_header, verify_api_key
from .session_utils import get_api_key, return_all_sessions_api_keys, get_user_token_developer_token, create_session, create_api_key, serializer, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from sqlalchemy.orm import Session
import numpy as np
from typing import List, Optional
from pathlib import Path
import pandas as pd
import json
import datetime
import os
import requests


router = APIRouter(prefix="/web", tags=["Web"])

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

@router.get("/genres/", response_model=schemas.Genres)
def get_distinct_genres(db: Session = Depends(get_db)):
    """
    Get distinct genres from the database, returned as a dictionary
    """
    db_genre = crud.get_unique_genres(db)
    x = {'genres': {}}
    for i in db_genre:
        if i[0] in x['genres']:
            x['genres'][i[0]].append(i[1])
        else:
            x['genres'][i[0]] = [i[1]]
    return x

@router.get("/publications/", response_model=schemas.Publications)
def get_distinct_publications(db: Session = Depends(get_db)):
    db_genre = crud.get_unique_publications(db)
    x = {'publications': {}}
    for i in db_genre:
        if i[0] in x['publications']:
            x['publications'][i[0]].append(i[1])
        else:
            x['publications'][i[0]] = [i[1]]
    return x

@router.get("/artists/", response_model=schemas.Artists)
def get_distinct_artists(db: Session = Depends(get_db)):
    db_artist = crud.get_artist_name_ids(db)
    x = {'artists': {}}
    for i in db_artist:
        x['artists'][i.artist_name] = i.artist_id
    return x

@router.get("/artists_albums/", response_model=schemas.AlbumsList)
def get_distinct_artists_albums(db: Session = Depends(get_db)):
    db_artist_albums = crud.get_unique_artists_albums(db)
    x = {'albums': []}
    for i in db_artist_albums:
        x['albums'].append({'album_id': i.album_id,
                            'album_name': i.album_name,
                            'artist': i.artist,
                            'artist_id': i.artist_id
                            })
    return x

@router.get("/albums_for_artist/{artist_id}", response_model=schemas.Albums)
def get_albums_for_artist(artist_id: str, db: Session = Depends(get_db)):
    db_album = crud.get_albums_for_artist(db, artist_id=artist_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    x = {'albums': {}}
    for position, value in enumerate(db_album):
        print(position, value, value[0], value[1])
        x['albums'][value[0]] = value[1]
    return x

@router.get("/tracks_for_artist/{artist_id}", response_model=schemas.TracksList)
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

@router.get("/tracks_for_album/{album_id}", response_model=schemas.TracksList)
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

@router.get("/tracks_for_albums/", response_model=schemas.TracksList)
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

@router.get("/random_track_from_artist/{artist_id}", response_model=schemas.Tracks)
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

@router.get("/random_track_from_album/{album_id}", response_model=schemas.Tracks)
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

@router.get("/get_relevant_albums/", response_model=schemas.Albums)
def get_relevant_albums(min_year: int, 
                        max_year: int, 
                        genre: List[str] = Query([None]), 
                        subgenre: List[str] = Query([None]), 
                        publication: List[str] =Query([None]), 
                        list: List[str] = Query([None]), 
                        points_weight: float = 0.5,
                        album_limit: int = 50,
                        db: Session = Depends(get_db)
                        ):
    """
    Return a list of relevant albums given a set of inputs

    Returned in dictionary format, used for Streamlit
    """
    output = {'albums': {}}
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
    for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True)[:album_limit]:
        output['albums'][value[0]] = value[1]
    return output

@router.get("/get_similar_artists_by_publication/{artist_id}", response_model=schemas.Artists)
def get_similar_artists_by_publication(artist_id: str, 
                        db: Session = Depends(get_db)
                        ):
    """
    Return a list of similar artists to a given artist ID by cosine similarity of placement in music publications

    Not used as an endpoint, but potentially useful in data exploration
    """
    return _get_similar_artists_by_publication(artist_id, db)

@router.get("/get_similar_albums_by_publication/{album_id}", response_model=schemas.Albums)
def get_similar_albums_by_publication(album_id: str, 
                                      restrict_genre: bool = True,
                                      db: Session = Depends(get_db)
                                      ):
    """
    Return a list of similar albums to a given album ID by cosine similarity of placement in music publications

    Not used as an endpoint, but potentially useful in data exploration
    """
    return _get_similar_albums_by_publication(album_id, restrict_genre, db)

@router.get("/get_similar_artists/{artist_id}", response_model=schemas.ArtistsList)
def get_similar_artists(artist_id: str,
                        n_artists: int = 10,
                        features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']),
                        unskew_features: bool = True,
                       db: Session = Depends(get_db)
                       ):
    """
    Return a list of similar artists to a given artist ID by cosine similarity of genres for albums listed in music publications

    Not used as an endpoint, but potentially useful in data exploration
    """
    # Similar Artists by Genre
    similar_artists_by_genre_raw = _get_similar_artists_by_genre(artist_id, db)
    similar_artists_by_genre = pd.DataFrame.from_dict(similar_artists_by_genre_raw['artists'], orient='index')
    similar_artists_by_genre.columns = ['genre_similarity']

    # Similar Artists by Publication
    similar_artists_by_publication_raw = _get_similar_artists_by_publication(artist_id, db)
    similar_artists_by_publication = pd.DataFrame.from_dict(similar_artists_by_publication_raw['artists'], orient='index')
    similar_artists_by_publication.columns = ['publication_similarity']
    # Similar Artists by Track Details
    similar_artists_by_track_details_raw = _get_similar_artists_by_track_details(artist_id, features, unskew_features, db)
    similar_artists_by_track_details = pd.DataFrame.from_dict(similar_artists_by_track_details_raw['artists'], orient='index')
    similar_artists_by_track_details.columns = ['track_details_similarity']

    # Combine all dataframes
    combined_similar_artists = pd.concat([similar_artists_by_genre, similar_artists_by_publication, similar_artists_by_track_details], axis=1)
    combined_similar_artists = similar_artists_by_genre.merge(similar_artists_by_publication, left_index=True, right_index=True).merge(similar_artists_by_track_details, left_index=True, right_index=True)
    combined_similar_artists = combined_similar_artists.reset_index().rename(columns={'index': 'artist_id'})

    # Normalize the similarity scores

    max_value = combined_similar_artists['track_details_similarity'].max()
    min_value = combined_similar_artists['track_details_similarity'].min()
    combined_similar_artists['track_details_similarity'] = (combined_similar_artists['track_details_similarity'] - min_value) / (max_value - min_value)
    combined_similar_artists['estimated_total_score'] = combined_similar_artists['genre_similarity'] * ((combined_similar_artists['publication_similarity'] * 0.5) + (combined_similar_artists['track_details_similarity'] * 0.5))
    combined_similar_artists = combined_similar_artists.sort_values(by='estimated_total_score', ascending=False).reset_index(drop=True)
    combined_similar_artists = combined_similar_artists.head(n_artists)
    x = {'artists': []}
    for index, row in combined_similar_artists.iterrows():
        x['artists'].append({
            'artist_id': row['artist_id'], 
            'track_details_similarity': row['track_details_similarity'],
            'publication_similarity': row['publication_similarity'],
            'genre_similarity': row['genre_similarity'],
            'estimated_total_score': row['estimated_total_score']
        })
    return x

@router.get("/get_similar_artists_by_genre/{artist_id}", response_model=schemas.Artists)
def get_similar_artists_by_genre(artist_id: str,
                                 db: Session = Depends(get_db)
                                 ):
    """
    Return a list of similar artists to a given artist ID by cosine similarity of genres for albums listed in music publications

    Not used as an endpoint, but potentially useful in data exploration
    """
    return _get_similar_artists_by_genre(artist_id=artist_id,
                                         db=db)

@router.get("/get_similar_genres/{genre}", response_model=schemas.Genres)
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

@router.get("/get_similar_tracks_by_euclidean_distance/{track_id}", response_model=schemas.Tracks)
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

@router.get("/get_similar_artists_by_track_details/{artist_id}", response_model=schemas.Artists)
def get_similar_artists_by_track_details(artist_id: str, 
                                         features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']), 
                                         unskew_features: bool = True, 
                                         db: Session = Depends(get_db)
                                         ):
    """
    Return a list of similar artist IDs to a given artist ID by euclidean distance of median musical features for each artist

    Not used as an endpoint, but potentially useful in data exploration
    """
    return _get_similar_artists_by_track_details(artist_id=artist_id,
                                features=features,
                                unskew_features=unskew_features,
                                db=db
                                )

@router.get("/get_similar_albums_by_track_details/{album_id}", response_model=schemas.Albums)
def get_similar_albums_by_track_details(album_id: str, 
                                         features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']),
                                         restrict_genre: bool = True,
                                         unskew_features: bool = True, 
                                         db: Session = Depends(get_db)
                                         ):
    """
    Return a list of similar artist IDs to a given artist ID by euclidean distance of median musical features for each artist

    Not used as an endpoint, but potentially useful in data exploration
    """
    return _get_similar_albums_by_track_details(album_id=album_id,
                                                features=features,
                                                restrict_genre=restrict_genre,
                                                unskew_features=unskew_features,
                                                db=db
                                                )

@router.get("/get_similar_albums/{album_id}", response_model=schemas.AlbumsList)
def get_similar_albums(album_id: str,
                       restrict_genre: bool = True,
                       features: List[str] = Query(['danceability', 'energy', 'instrumentalness', 'valence', 'tempo']),
                       unskew_features: bool = True,
                       n_albums: int = 10,
                       db: Session = Depends(get_db)
                       ):
    """
    Return a list of similar album IDs to a given album ID by cosine similarity of placement in music publications and euclidean distance of median musical features
    """

    # Get similar albums by publication
    similar_albums_by_publication_raw = _get_similar_albums_by_publication(album_id, restrict_genre=restrict_genre, db=db)
    similar_albums_by_publication = pd.DataFrame.from_dict(similar_albums_by_publication_raw['albums'], orient='index')
    similar_albums_by_publication.columns = ['publication_similarity']

    # Get similar albums by track details
    similar_albums_by_track_details_raw = _get_similar_albums_by_track_details(album_id, features=features, restrict_genre=restrict_genre, unskew_features=unskew_features, db=db)
    similar_albums_by_track_details = pd.DataFrame.from_dict(similar_albums_by_track_details_raw['albums'], orient='index')
    similar_albums_by_track_details.columns = ['track_details_similarity']

    # Combine the two lists
    combined_similar_albums = similar_albums_by_publication.merge(similar_albums_by_track_details, left_index=True, right_index=True)
    combined_similar_albums = combined_similar_albums.reset_index().rename(columns={'index': 'album_id'})

    # Normalize the similarity scores
    combined_similar_albums['track_details_similarity'] = combined_similar_albums['track_details_similarity'].max() - combined_similar_albums['track_details_similarity']
    max_value = combined_similar_albums['track_details_similarity'].max()
    min_value = combined_similar_albums['track_details_similarity'].min()
    combined_similar_albums['track_details_similarity'] = (combined_similar_albums['track_details_similarity'] - min_value) / (max_value - min_value)
    combined_similar_albums['estimated_total_score'] = (combined_similar_albums['track_details_similarity'] * 0.5) + (combined_similar_albums['publication_similarity'] * 0.5)
    combined_similar_albums = combined_similar_albums.sort_values(by='estimated_total_score', ascending=False).reset_index(drop=True)
    combined_similar_albums = combined_similar_albums.head(n_albums)

    # Get Album Info
    db_albums = crud.get_album_info(db=db,
                                    album_uris=list(combined_similar_albums['album_id']))
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")

    x = {'albums': []}
    for album in db_albums:
        x['albums'].append({
            'album_id': album.album_uri, 
            'album': album.album,
            'artist': album.artist,
            'image_url': album.image_url,
            'album_url': album.album_url,
            'year': album.year,
            'genre': album.genre,
            'subgenre': album.subgenre,
            'track_details_similarity': combined_similar_albums[combined_similar_albums['album_id'] == album.album_uri]['track_details_similarity'].values[0],
            'publication_similarity': combined_similar_albums[combined_similar_albums['album_id'] == album.album_uri]['publication_similarity'].values[0],
            'estimated_total_score': combined_similar_albums[combined_similar_albums['album_id'] == album.album_uri]['estimated_total_score'].values[0]
        })
    # Return the combined list
    x['albums'] = sorted(x['albums'], key=lambda x: x['estimated_total_score'], reverse=True)
    return x
    
    
    
    


@router.get('/get_similar_tracks/{track_id}', response_model=schemas.TracksList)
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

@router.get('/get_track_data/{track_id}', response_model=schemas.TrackDetails)
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

@router.get('/get_album_accolades_multiple_albums/', response_model=schemas.Albums)
def get_album_accolades_multiple_albums(album_ids: List[str] = Query([None]),
                                        n_accolades: int = 10,
                                        album_limit: int = 50,
                                        db: Session = Depends(get_db),
                                        exclude_accolades_only_one_point: bool = True
                                        ):
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
        album_key = getattr(value, 'album_key')
        if album_key in x['albums']:
            pass
        else:
            x['albums'][album_key] = []
        new_value = {}
        for feature in ['rank', 'points', 'publication', 'list']:
            new_value[feature] = getattr(value, feature)
        x['albums'][album_key].append(new_value)
    for album in x['albums']:
        new_dict = []
        counting_value = 0
        if len(x['albums'][album]) == 1:
            skip_low_points_value = False
        else:
            skip_low_points_value = exclude_accolades_only_one_point
        for value in sorted(x['albums'][album], key=lambda x: x['points'], reverse=True):
            if skip_low_points_value:
                if value['points'] == 1:
                    continue
            new_dict.append(value)
            counting_value += 1
            if counting_value >= n_accolades:
                break
        x['albums'][album] = new_dict
    return x

@router.get('/get_tracks_by_features/', response_model=schemas.Tracks)
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

@router.get("/get_apple_developer_token/")
def get_apple_developer_token(api_key: str = Depends(verify_api_key)):
    return _get_apple_music_auth_header(api_key)

@router.get("/get_apple_music_auth_page/", response_class=HTMLResponse)
def get_apple_music_auth_page(request: Request):
    api_key = os.getenv('API_KEY')
    developer_token_dict = _get_apple_music_auth_header(api_key)
    developer_token = developer_token_dict['developer_token']
    return templates.TemplateResponse("apple_music_auth.html", 
    {"request": request, 
    "developer_token": developer_token
    })

@router.get("/get_relevant_lists/", response_model=schemas.Lists)
def get_relevant_lists(min_year: int, 
                        max_year: int, 
                        genre: List[str] = Query([None]), 
                        subgenre: List[str] = Query([None]), 
                        publication: List[str] = Query([None]),
                        db: Session = Depends(get_db),
                        ignore_monthly_lists: bool = False
                        ):
    db_lists = crud.get_relevant_lists(db, min_year=min_year, max_year=max_year, genre=genre, subgenre=subgenre, publication=publication)
    if db_lists is None:
        raise HTTPException(status_code=404, detail="No lists that match criteria")
    elif len(db_lists) == 0:
        raise HTTPException(status_code=404, detail="No lists that match criteria")
    x = {'lists': []}
    for list in db_lists:
        if ignore_monthly_lists:
            if 'January' in list.list or 'February' in list.list or 'March' in list.list or 'April' in list.list or 'May' in list.list or 'June' in list.list or 'July' in list.list or 'August' in list.list or 'September' in list.list or 'October' in list.list or 'November' in list.list or 'December' in list.list or 'Spring' in list.list or 'Summer' in list.list or 'Fall' in list.list or 'Winter' in list.list: # ew lol
                continue
            else:
                x['lists'].append(list.list)
        else:
            x['lists'].append(list.list)
    x['lists'] = sorted(x['lists'])
    return x

@router.post("/create_session_endpoint/")
async def create_session_endpoint(token_request: schemas.UserTokenRequest, response: Response):
    """
    Create a session after successful authorization and set secure cookie
    """
    user_token = token_request.user_token
    if not user_token:
        raise HTTPException(status_code=400, detail="No user token provided")

    session_id = create_session(user_token)
    api_key = create_api_key(session_id)
    signed_session = serializer.dumps(session_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME, 
        value=signed_session,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/"
        )
    return {
        "success": True, 
        "message": "Session created successfully",
        # "redirect_url": f"https://localhost:8501/?api_key={api_key}"
        "redirect_url": f"https://topmusic.lol/?api_key={api_key}"
        }

@router.get("/get_all_api_keys/")
async def get_all_api_keys(api_key: str = Depends(verify_api_key)):
    """
    Get all API keys
    """
    return return_all_sessions_api_keys()

@router.get("/get_user_apple_library/")
async def get_user_apple_library(session_info: dict = Depends(get_api_key)):
    USER_TOKEN, DEVELOPER_TOKEN = get_user_token_developer_token(session_info)
    headers = {
        'Authorization': f'Bearer {DEVELOPER_TOKEN}',
        'Music-User-Token': USER_TOKEN
    }
    response = requests.get('https://api.music.apple.com/v1/me/library/songs?limit=1', headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

@router.post("/create_apple_music_playlist/")
async def create_apple_music_playlist(session_info: dict = Depends(get_api_key), tracks: List[str] = Query([None]), playlist_name: str = Query(None)):
    """
    Create an Apple Music playlist
    """
    USER_TOKEN, DEVELOPER_TOKEN = get_user_token_developer_token(session_info)
    headers = {
        'Authorization': f'Bearer {DEVELOPER_TOKEN}',
        'Music-User-Token': USER_TOKEN,
        'Content-Type': 'application/json'
    }
    tracks_data = [{"id": track, "type": "songs"} for track in tracks]

    playlist_name = f'{playlist_name} Radio'
    playlist_json = {
    "attributes": {"description": "created via TopMusic", 
                    "name": playlist_name},
    "relationships": {"tracks": {"data": tracks_data}}
    }

    response = requests.post('https://api.music.apple.com/v1/me/library/playlists', headers=headers, json=playlist_json)
    if response.status_code == 201:
        return response.json()
    else:
        return None