from ..database import get_db
from .. import crud, models, schemas
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ._utils import *

router = APIRouter(prefix="/app", tags=["Mobile App"])

@router.get("/genres/", response_model=schemas.GenresList)
def get_distinct_genres(db: Session = Depends(get_db)):
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

@router.get("/artists/", response_model=schemas.ArtistsList)
def get_distinct_artists(db: Session = Depends(get_db)):
    db_artist = crud.get_artist_name_ids(db)
    x = {'artists': []}
    for i in db_artist:
        x['artists'].append({'name': i.artist, 'id': i.artist_id})
    return x

@router.get("/artist_id_from_artist_name/", response_model=schemas.ArtistsList)
def get_artist_id_from_artist_name(artist_name: str, db: Session = Depends(get_db)):
    db_artist = crud.get_artist_id_from_name(db, artist_name=artist_name)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    x = {'artists': []}
    for i in db_artist:
        x['artists'].append({'name': i.artist, 'id': i.artist_id})
    return x

@router.get("/get_relevant_albums_new/", response_model=schemas.AlbumsList)
def get_relevant_albums_new(min_year: int, 
                            max_year: int, 
                            genre: List[str] = Query([None]), 
                            subgenre: List[str] = Query([None]), 
                            publication: List[str] =Query([None]), 
                            list: List[str] = Query([None]), 
                            points_weight: float = 0.5,
                            randomize: bool = False,
                            order_by_recency: bool = False,
                            album_limit: int = 50,
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
    if order_by_recency:
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['album_key'], reverse=True)[:album_limit]:
            new_dict.append(value[1])
    else:
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True)[:album_limit]:
            new_dict.append(value[1])
    x['albums'] = new_dict
    return x

@router.get("/get_recommended_tracks/", response_model=schemas.TracksList)
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
                                 max_year=2025, 
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
        np.random.shuffle(tracks)
        x = {'tracks': []}
        for track in tracks:
            x['tracks'].append(track)
        return x

@router.get('/get_album_accolades/', response_model=schemas.AlbumsList)
def get_album_accolades(album_id: str = Query(None),
                        n_accolades: int = 10,
                        db: Session = Depends(get_db)):
    """
    Return a dictionary of album accolades given a single album URI
    """
    db_albums = crud.get_album_accolades(db, album_id=album_id)
    if db_albums is None:
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

@router.get("/return_tracks_from_albums/", response_model=schemas.TracksList)
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

@router.get("/get_artists_from_search_string/", response_model=schemas.ArtistsList)
def get_artists_from_search_string(search_string: str, db: Session = Depends(get_db)):
    """
    Return a list of artists given a search string
    """
    db_artists = crud.get_relevant_artists(db, search_string)
    print(len(db_artists))
    x = {'artists': []}
    for i in db_artists:
        x['artists'].append({'name': i.artist, 'id': i.artist_id})
    return x



